import sys
import os

# Fügen Sie den Pfad zu Ihrem benutzerdefinierten Modul-Verzeichnis hinzu
sys.path.insert(0, "/www/htdocs/w01a6aec/python-module")

import anthropic
import backoff
import json
import random
from concurrent.futures import ThreadPoolExecutor
import time as t
from openai import OpenAI
import re
import json
from dotenv import load_dotenv


load_dotenv()  # Lädt die Variablen aus .env

@backoff.on_exception(
    backoff.expo,  # Exponential backoff strategy
    anthropic.APIError,      # Replace this with the specific exception from your API client if available
    max_time=300   # Maximum time (in seconds) for total retries
)
def generate_intro_section(content):

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


    INTRO_EXAMPLES = """
<example 1> Breakfast has always been my favorite meal. I look forward to special holiday breakfasts as much as I do the holiday ham for dinner. But that doesn't mean I want a sink full of dishes to clean before I've had my coffee. I prefer making breakfast before heading off to bed.

That's why breakfast casseroles are my breakfast hero during the holidays. I'll either bake one all the way through and warm it up in the morning, or if I'm making a bread-based casserole, then I'll assemble it and bake it in the morning. I prep the ingredients when I'm in the kitchen making dinner. No extra cutting boards to wash.

Love sausage, egg, and cheese? I've got a casserole for you. More into sweet and fruity? Same. Honestly, I'll make one of each and save myself from having to choose. </example 1> 


<example 2> I was an adult before I knew it was possible to successfully cook bacon any other way than in the microwave. It's how my mom always did it. When dad did it on the stove, it burned to a crisp.

That's because dad's bacon cooking technique was off—he was using high heat, and bacon in a skillet likes it low and slow. Microwave bacon, on the other hand, requires no technique outside of pressing buttons. For the cooking-impaired, it's foolproof. </example 2>

<example 3> Figuring out a go-to, healthy breakfast for hectic weekday mornings can be a major challenge. After all, healthy breakfasts are rarely attainable when you're up against the clock to catch your train on time, or beat the inevitable traffic jams on your daily commute, and things get even more challenging when kids are involved.

Luckily, these kale and mushroom egg bites check all the boxes: they're healthy yet delicious, simple to meal prep and reheat, and endlessly adaptable to whatever ingredients you have on hand. </example 3>


<example 4> Here is my favorite apple pie recipe, with an easy, no-fail, buttery, flaky homemade pie crust, and a filling with a mix of different types of apples, spices, vanilla, and a splash of brandy.

This apple pie is my family's most requested pie during the holidays. I usually make two of them so we can enjoy one for leftovers. Nothing better than pie for breakfast, right? </example 4>

<example 5> If you ask me, chopped salads are a genius invention.

This main dish Tex-Mex inspired salad makes a family-friend supper that's teaming with texture and flavor. Crunchy vegetables and sweet corn pair with a tangy, cilantro-flecked dressing.

It's tossed with chicken thighs dredged in old-school taco seasoning mix and cooked in a hot skillet. Crunchy tortilla chips and salty Cotija cheese help the whole thing come together.

It's a crowd-pleasing dish that runs on the lighter side, a perfect warm weather meal. </example 5> """


    # Split the string into examples
    examples = INTRO_EXAMPLES.split('<example')[1:]

    # Randomly select an example and get its index
    selected_index = random.randint(0, len(examples) - 1)
    selected_example = examples[selected_index].split('</example')[0].strip()

    # Print which example was chosen
    #print(f"Using example {selected_index + 1}")

    PROMPT=f"""
You are tasked with writing an introductory paragraph for a recipe blog article. The recipe you'll be introducing is:

<recipe_name>
{content}
</recipe_name>

When writing the intro, follow these guidelines and persona:

1. Use a casual, conversational tone as if you're talking to a friend.
2. Write at a 10th-grade English level - keep it simple and easy to understand.

Persona (only include personal details when the example intro uses them also!):
- Name: Molly Brown
- Age: 42
- Family: Married, 2 children
- Location: Portland
- Background: Grew up in an American household
- Occupation: Food blogger who loves sharing cooking tips and recipes

Avoid the following:
- Do not use these words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
- Refrain from using strong adjectives.

Your intro should mimic the style, tone, and sentence structure of this example:

<example>
{selected_example}
</example>

ONLY REPLY WITH THE INTRO NOTHING ELSE!!
"""

    
    try:
        message = client.messages.create(
            #client.chat.completions.create(
            model="claude-3-5-sonnet-latest",
            #model="gpt-4o",
            max_tokens=500,
            temperature=1,
            messages=[

                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT
                        }
                    ]
                }
            ]
        )
        return message.content[0].text
        #return message.choices[0].message.content

    except Exception as e:
        return f"API-Fehler: {str(e)}"

# Function to generate Recipe Section MAIN INGREDIENT
@backoff.on_exception(
    backoff.expo,  # Exponential backoff strategy
    anthropic.APIError,      # Replace this with the specific exception from your API client if available
    max_time=300   # Maximum time (in seconds) for total retries
)
def generate_maine_ingredient_section(title, ingredients):


    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about the main ingredient of the recipe. Follow these steps:

1. The recipe name is provided in the following tags:
<recipe_name>

</recipe_name>

2. The ingredient list for the recipe is provided in the following tags:
<ingredient_list>

</ingredient_list>

3. Identify the main ingredient from the ingredient list. 

4. Create a headline in the format "Which Kind of [Main Ingredient] Should I Use?" Replace [Main Ingredient] with the actual main ingredient you identified.

5. Write a paragraph about the main ingredient, following these guidelines:
   - Use a casual, conversational tone as if you're talking to a friend
   - Write at a 10th-grade English level - keep it simple and easy to understand
   - Structure your section as a single paragraph of 3-5 sentences
   - Discuss different varieties or types of the main ingredient that could be used in the recipe
   - Mention any tips for selecting or preparing the ingredient

6. Your section should mimic the style, tone, and sentence structure of this example (but not the content!):

Example:
"You can choose farm-raised or wild for this recipe, both will work. And, if all you have access to is frozen salmon, you'll still be good to go. In fact, most fresh salmon at the supermarket has been previously frozen right off the boat. Just be sure it was handled properly by checking for any visible ice crystals or signs of freezer burn.

For this recipe, you'll want to use skinless salmon. Arguably the best thing about salmon skin is getting it nice and crispy. Since we're cooking this salmon in a foil packet, that crispness won't be achieved and so it's best to do without it."

7. Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating. Also, refrain from using strong adjectives.

8. Format your output as follows:
   - Put the headline inside <h2> tags

Here's an example of how your output should be structured (but remember to use your own content based on the recipe):

<h2>What Kind of [Main Ingredient] Should I Use?</h2>
[Your 3-5 sentence paragraph goes here]

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
                {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "1. The recipe name is provided in the following tags:\n<recipe_name>\nFluffy Cottage Cheese Cloud Bread (Made in under 45 Minutes)\n</recipe_name>\n\n2. The ingredient list for the recipe is provided in the following tags:\n<ingredient_list>\n6 eggs, separated (room temperature)\n½ teaspoon white vinegar\n4 ounces cottage cheese\n½ teaspoon baking powder\n¼ teaspoon salt\n¾ cup whey protein powder\n¼ cup egg white protein powder\n1 tablespoon Allulose (optional)\nOptional toppings: bagel seasoning\n1 teaspoon vanilla extract (optional for French Toast only)\n</ingredient_list>"
                }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "<h2>What Kind of Cottage Cheese Should I Use?</h2>\nWhen making cloud bread, the type of cottage cheese you choose can make a difference in your final result. Small or medium curd cottage cheese works best since it blends more smoothly into the mixture, though large curd will also work if you blend it well. \n\nFor the best texture, I recommend using full-fat cottage cheese rather than low-fat varieties, as it helps create a richer, more satisfying bread. \n\nIf you're worried about lumps, you can give your cottage cheese a quick pulse in the food processor or blender before adding it to your recipe - this will help it incorporate more easily with the other ingredients."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text
    except Exception as e:
        print(f"ERROR: {e}")

    html_section= ""
    html_section += f"{section}\n"
    html_section += "<div class=\"hr--handdrawn\"></div>"

    return html_section

@backoff.on_exception(
    backoff.expo,  # Exponential backoff strategy
    anthropic.APIError,      # Replace this with the specific exception from your API client if available
    max_time=300   # Maximum time (in seconds) for total retries
)
def generate_serving_section(title, ingredients):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about what to serve with the recipe. Follow these steps:

1. The recipe name is provided in the following tags:

<recipe_name>

</recipe_name>

2. The ingredient list for the recipe is provided in the following tags:

<ingredient_list>

</ingredient_list>

3. Create a headline in the format "What to Serve With [dish]?" Replace [dish] with the actual dish. To determine the dish name:
   - If the recipe name is long or contains additional information (e.g., "Fluffy Cottage Cheese Cloud Bread (Made in under 45 Minutes)"), simplify it to the core dish (e.g., "cottage cheese cloud bread").
   - Use your judgment to extract the main dish name from the recipe title.

4. Write a paragraph about what to serve with the dish, following these guidelines:
   - Use a casual, conversational tone as if you're talking to a friend
   - Write at a 10th-grade English level - keep it simple and easy to understand
   - Structure your section as a single paragraph of 3-5 sentences
   - Consider the main ingredients and flavors of the dish when suggesting pairings
   - Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
   - Refrain from using strong adjectives

5. Your section should mimic the style, tone, and sentence structure of this example (but not the content!):

Example:
"My favorite way to serve beans and greens is with crusty Italian bread (of course!). I often transform greens and beans into a soup so there's even more dipping to be done. To do so, add a few extra cups of broth, a can of diced tomatoes, and short pasta like orzo or ditalini. Bring everything to a simmer until the pasta is cooked, adding extra broth as needed, and finishing with plenty of lemon and fresh parsley.

I also like eating beans and greens:

With crumbled or sliced Italian sausage
With sliced chicken cutlets 
On top of cooked pasta like penne, rotini, or ziti
Over white rice"

6. Format your output as follows:
   - Put the headline inside <h2> tags
   - Place the paragraph immediately after the headline, without any additional tags

Your output should be structured like this:

<h2>What to Serve With [dish]?</h2>
[Your 3-5 sentence paragraph goes here]

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. Use the recipe name and ingredient list to inform your suggestions for pairings."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "1. The recipe name is provided in the following tags:\n\n<recipe_name>\nCreamy Tomato Soup with Heavy Cream\n</recipe_name>\n\n2. The ingredient list for the recipe is provided in the following tags:\n\n<ingredient_list>\n2 cans whole peeled tomatoes (28 ounces each)\n1 quart chicken stock\n2 heaping tablespoons finely chopped garlic\n1 cup heavy whipping cream\n1 cup grated parmesan cheese\n1 teaspoon salt\n1 teaspoon black pepper\n</ingredient_list>"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "<h2>What to Serve With Tomato Soup?</h2>\nNothing beats the classic combo of tomato soup and a grilled cheese sandwich - it's basically a match made in comfort food heaven! \n\nFor the perfect grilled cheese pairing, go for a mix of cheeses like cheddar and mozzarella on thick-cut sourdough bread, which is great for dunking into this creamy soup. \n\nIf you're looking to keep things lighter, a simple green salad with balsamic dressing works really well, or try some garlic bread to soak up every last drop of the soup. \n\nFor a fun twist, you can even top your soup with some crunchy croutons or a handful of oyster crackers for added texture."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text
    except Exception as e:
        print(f"ERROR: {e}")

    html_section= ""
    html_section += f"{section}\n"
    html_section += "<div class=\"hr--handdrawn\"></div>\n"

    return html_section

@backoff.on_exception(
    backoff.expo,  # Exponential backoff strategy
    anthropic.APIError,      # Replace this with the specific exception from your API client if available
    max_time=300   # Maximum time (in seconds) for total retries
)
def generate_doneness_section(title, ingredients):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about how to know when the dish is done. Follow these steps:

1. The recipe name is provided in the following tags:

<recipe_name>

</recipe_name>

2. The ingredient list for the recipe is provided in the following tags:

<ingredient_list>

</ingredient_list>

3. Create a headline in the format "How to Know When the [dish] is Done" Replace [dish] with the actual dish. To determine the dish name:
   - If the recipe name is long or contains additional information (e.g., "Fluffy Cottage Cheese Cloud Bread (Made in under 45 Minutes)"), simplify it to the core dish (e.g., "cottage cheese cloud bread").
   - Use your judgment to extract the main dish name from the recipe title.

4. Write a paragraph about how to know when the dish is done, following these guidelines:
   - Use a casual, conversational tone as if you're talking to a friend
   - Write at a 10th-grade English level - keep it simple and easy to understand
   - Structure your section as a single paragraph of 3-5 sentences
   - Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
   - Refrain from using strong adjectives

5. Your section should mimic the style, tone, and sentence structure of this example (but not the content!):

Example:
"If you can't tell if it's done: I recommend letting the rice steam for the amount of time indicated in the recipe, but if you are unsure after that time has elapsed, you can use a spatula to lift the rice slightly from the side of the pan and see if the grains are a deep saffron color and crunchy. 
If it's not crispy enough: All pots, brands of rice, and stovetops are different, so it may be a case of trial and error the first few times you make it. You may have to allow the rice to cook another 5 to 10 minutes or turn the burner up slightly from low to medium-low."

5. Format your output as follows:
   - Put the headline inside <h2> tags
   - Place the paragraph immediately after the headline, without any additional tags

Your output should be structured like this:

<h2>How to Know When the [dish] is Done</h2>
[Your 3-5 sentence paragraph goes here]

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. Use the recipe name and ingredient list to inform your suggestions about how to know when the dish is done.
"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "1. The recipe name is provided in the following tags:\n\n<recipe_name>\nEasy Egg Hashbrown Casserole\n</recipe_name>\n\n2. The ingredient list for the recipe is provided in the following tags:\n\n<ingredient_list>\n2 pounds thawed frozen hash brown potatoes\n1 pound pork sausage\n1 small diced onion\n5 eggs\n1/2 cup milk\n1/2 teaspoon onion powder\n1/8 teaspoon garlic powder\nSalt to taste\nBlack pepper to taste\n12 ounces shredded cheddar cheese\n</ingredient_list>\n"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "<h2>How to Know When the Hashbrown Casserole is Done</h2>\nYour hashbrown casserole is ready when the edges turn golden brown and the center is set - this usually takes about 45-50 minutes in the oven. \n\nTo check if it's fully cooked, insert a knife into the middle - it should come out clean without any wet egg mixture clinging to it. \n\nThe cheese on top should be completely melted and lightly browned, and when you gently press the center with a spatula, it shouldn't feel jiggly or soft. \n\nLet it rest for about 5 minutes after taking it out of the oven so it can set up properly."
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text
    except Exception as e:
        print(f"ERROR: {e}")

    html_section= ""
    html_section += f"{section}\n"
    html_section += "<div class=\"hr--handdrawn\"></div>"

    return html_section

@backoff.on_exception(backoff.expo, anthropic.APIError,  max_time=300)
def generate_new_storage_section(title, ingredients):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about storage instructions and, if necessary, about making ahead. Follow these steps:

1. The recipe name is provided in the following tags:

<recipe_name>

</recipe_name>

2. The ingredient list for the recipe is provided in the following tags:

<ingredient_list>

</ingredient_list>

3. Write a paragraph about storage instructions, and if necessary about making ahead, following these guidelines:
   - Use a casual, conversational tone as if you're talking to a friend
   - Write at a 10th-grade English level - keep it simple and easy to understand
   - Do not always use the same storage instructions "Store", "Freeze" and "Reheat", they are not fix. Always switch the storage instructions that are 
   - Write about 1-2 sentences per storage description.
matching recipe - For example: Do not use "Reheat" for a cold recipe. Use your common sense.
   - Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
   - Refrain from using strong adjectives

4. Your paragraph should mimic the style, tone, and sentence structure of this example (but not the content!) and must be in JSON format:

Example:
"
{
  "storage instructions": [
    {
      "storage instruction": "Store",
      "description": "Broccoli cheese soup stores well. Keep it in an airtight container in the refrigerator for up to 5 days. I love making this ahead for the week, because it tastes just as good for days! I often enjoy it for lunch with a Caprese salad, or a Big Mac salad when I want something more hearty."
    },
    {
      "storage instruction": "Freeze",
      "description": "I often have individual portions of this soup stashed in my freezer for lunch. Simply let it cool to room temperature, then freeze flat in freezer bags or in a freezer safe container for up to 3 months."
    },
    {
      "storage instruction": "Reheat",
      "description": "Warm up the soup on the stove top over low heat, or in the microwave on medium to low power. Sometimes it separates a bit after a while, but usually comes back together after you reheat while stirring frequently. If that doesn't help, you can also puree it in a blender to bring it back together."
    }
  ]
}
"

5. Format your output as follows:
   - Put the headline "Storage Instructions" inside <h2> tags
   - Place the JSON output immediately after the headline, without any additional text.

Your output should be structured like this:

<h2>Storage Instructions</h2>
[JSON output here]

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. Use the recipe name and ingredient list to inform your suggestions about storage and make-ahead options.
"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "1. The recipe name is provided in the following tags:\n\n<recipe_name>\nFluffy Cottage Cheese Cloud Bread (Made in under 45 Minutes)\n</recipe_name>\n\n2. The ingredient list for the recipe is provided in the following tags:\n\n<ingredient_list>\n6 eggs, separated (room temperature)\n½ teaspoon white vinegar\n4 ounces cottage cheese\n½ teaspoon baking powder\n¼ teaspoon salt\n¾ cup whey protein powder\n¼ cup egg white protein powder\n1 tablespoon Allulose (optional)\nOptional toppings: bagel seasoning\n1 teaspoon vanilla extract (optional for French Toast only)\n</ingredient_list>"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "<h2>Storage Instructions</h2>\n{\n  \"storage instructions\": [\n    {\n      \"storage instruction\": \"Keep Fresh\",\n      \"description\": \"Your cloud bread will stay nice and fluffy when stored in an airtight container with parchment paper between each piece. Pop it in the fridge and it'll keep well for up to 4 days. Just make sure to let the bread cool completely before storing to prevent any condensation from making it soggy.\"\n    },\n    {\n      \"storage instruction\": \"Freeze\",\n      \"description\": \"These little clouds freeze beautifully! Layer them between pieces of parchment paper in a freezer-safe container or zip-top bag and they'll keep for up to 2 months. This is perfect for meal prep or when you want to make a bigger batch to have on hand.\"\n    },\n    {\n      \"storage instruction\": \"Serve\",\n      \"description\": \"When you're ready to enjoy your cloud bread from the fridge or freezer, just let it come to room temperature for about 15-20 minutes. If you like it warm, you can pop it in a toaster on low heat for a quick crisp-up. The texture might be slightly different from fresh, but it's still tasty!\"\n    }\n  ]\n}"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text
        html_section=''
    except Exception as e:
        print(f"ERROR: {e}")
        
        # Parse JSON content if section contains ingredients
    
    if '"storage instructions":' in section:
        try:
            # Extract h2 title
            h2_end = section.find('\n{')
            title = section[:h2_end]
            
            # Parse JSON
            json_str = section[h2_end:]
            data = json.loads(json_str)
            
            # Build HTML
            html_section += f"{title}\n"
            
            for storage in data['storage instructions']:
                instruction = storage['storage instruction']
                description = storage['description']
                html_section += f"<i><strong>{instruction}</strong></i>: {description}</li><br>\n"
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            html_section += f"{section}\n"
    
    else:
        html_section += f"{section}\n"
        
    html_section += "<div class=\"hr--handdrawn\"></div>\n"

    return html_section

@backoff.on_exception(backoff.expo, anthropic.APIError,  max_time=300)
def generate_new_substitution_section(title, ingredients):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about ingredient substitutions for the following recipe:

The recipe name is:
<recipe_name>

</recipe_name>

The ingredient list for this recipe is:

<ingredient_list>

</ingredient_list>

Write a paragraph about ingredient substitutions by following these guidelines:
- Based on the main ingredients of the provided list, make suggestions for substitutions. Also suggest to not substitute an ingredient, if it is absolutely necessary for the recipe (e.g. risotto rice for a risotto).
- Mention also if there are any changes to make in the recipe, and if yes, how to prepare the substitute, if necessary.
- Use a casual, conversational tone as if you're talking to a friend
- Write at a 10th-grade English level - keep it simple and easy to understand
- Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
- Refrain from using strong adjectives

Your paragraph should mimic the style, tone, and sentence structure of this example (but not the content!) and must be in JSON format:


JSON:
"
{
  "Intro": [
    {
      "text": "The best part of this recipe? It lends itself to a few swaps and subs if needed:",
      "ingredients": [
        {
          "ingredient": "African bird's eye chili",
          "description": "If you don't have African bird's eye chili on hand that's ok. Try using other hot peppers like Thai chili, serrano peppers, habaneros, or scotch bonnet peppers."
        },
        {
          "ingredient": "Chicken leg quarters",
          "description": "I used leg quarters for this recipe, but you can always use just chicken leg or thigh portions."
        },
        {
          "ingredient": "Chili peppers",
          "description": "This chicken is spicy, but you can omit 1 to 2 peppers to decrease the heat if your family isn't too fond of spice."
        },
        {
          "ingredient": "Red wine vinegar",
          "description": "If you don't have red wine vinegar on hand, you can use white vinegar and still get that tangy taste."
        }
      ]
    }
  ]
}
"


Format your output as follows:
- Put the headline "Options for Substitutions" inside <h2> tags
- Place the JSON output after the headline, without any other content

Your output should be structured like this:

<h2>Options for Substitutions</h2>
{json output here}

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. Use the recipe name and ingredient list to inform your suggestions about substitutions."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "The recipe name is:\n<recipe_name>\nWholesome Crockpot Beef Stew\n</recipe_name>\n\nThe ingredient list for this recipe is:\n\n<ingredient_list>\n2 ½ pounds of stew meat\n½ teaspoon each of black pepper, garlic salt, and celery salt\n1/4 cup flour\n3-6 tablespoons olive oil\n3 tablespoons chilled butter (split)\n2 cups chopped yellow onions\n4 minced garlic cloves\n1 cup cabernet sauvignon or merlot wine\n4 cups beef stock\n2 beef bouillon cubes\n2 tablespoons worcestershire sauce\n3 tablespoons tomato concentrate\n5 medium carrots, chopped into 1-inch pieces\n1 pound baby yukon gold potatoes, halved or quartered\n2 bay leaves\n1 rosemary sprig\n1 cup frozen peas\n1/4 cup cold water mixed with 3 tablespoons corn starch (optional)\n2-3 drops gravy master (optional for a deeper color)\n</ingredient_list>"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": "<h2>Options for Substitutions</h2>\n{\n  \"Intro\": [\n    {\n      \"text\": \"Good news - this hearty stew recipe is pretty flexible when it comes to substitutions:\",\n      \"ingredients\": [\n        {\n          \"ingredient\": \"Stew meat\",\n          \"description\": \"While beef chuck is traditional for stew, you can use other tough cuts like bottom round, brisket, or even lamb shoulder for a different take. Just make sure to choose well-marbled meat that can handle long cooking times.\"\n        },\n        {\n          \"ingredient\": \"Wine\",\n          \"description\": \"Don't have wine? No problem! Replace it with additional beef stock plus 1 tablespoon of balsamic vinegar to add that rich depth of flavor.\"\n        },\n        {\n          \"ingredient\": \"Yukon gold potatoes\",\n          \"description\": \"Red potatoes or russets work just as well. If using russets, cut them slightly larger as they tend to break down more easily.\"\n        },\n        {\n          \"ingredient\": \"Beef stock and bouillon\",\n          \"description\": \"Store-bought stock is fine, but if you're out, you can use chicken stock in a pinch. Just add an extra bouillon cube to maintain that rich beef flavor.\"\n        },\n        {\n          \"ingredient\": \"Cornstarch\",\n          \"description\": \"For thickening, you can swap cornstarch with flour (use 6 tablespoons mixed with cold water) or instant potato flakes (start with ¼ cup and adjust as needed).\"\n        },\n        {\n          \"ingredient\": \"Frozen peas\",\n          \"description\": \"Feel free to swap these with frozen green beans or corn, or leave them out entirely if you're not a fan of peas.\"\n        }\n      ]\n    }\n  ]\n}"
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text
        html_section=''
    except Exception as e:
        print(f"ERROR: {e}")
        
        # Parse JSON content if section contains ingredients
    
    if '"ingredients":' in section:
        try:
            # Extract h2 title
            h2_end = section.find('\n{')
            title = section[:h2_end]
            
            # Parse JSON
            json_str = section[h2_end:]
            data = json.loads(json_str)
            
            # Build HTML
            html_section += f"{title}\n"
            
            # Add intro text if present
            if data['Intro'][0]['text']:
                html_section += f"<p>{data['Intro'][0]['text']}</p>\n"
            
            html_section += "<ul class='feature-list'>\n"
            
            for ingredient in data['Intro'][0]['ingredients']:
                html_section += f"<li><strong>{ingredient['ingredient']}</strong>: {ingredient['description']}</li>\n"
                
            html_section += "</ul>\n"
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            html_section += f"{section}\n"
    else:
        html_section += f"{section}\n"
        
    html_section += "<div class=\"hr--handdrawn\"></div>\n"

    return html_section

@backoff.on_exception(
    backoff.expo, 
    anthropic.APIError,  # Only retry on Anthropic API errors
    max_time=300
)
def generate_whylove_section(title, ingredients, time):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about why you will love this recipe for the following recipe:

1. The recipe name is:
<recipe_name>

</recipe_name>

2. The ingredient list for this recipe is:
<ingredient_list>

</ingredient_list>

3. Create a headline in the format "Why You'll Love This [dish]" Replace [dish] with the actual dish. To determine the dish name:
- If the recipe name is long or contains additional information (e.g., "Fluffy Cottage Cheese Cloud Bread (Made in under 45 Minutes)"), simplify it to the core dish (e.g., "cottage cheese cloud bread").
- Use your judgment to extract the main dish name from the recipe title.

4. Write a paragraph about why you will love the recipe by following these guidelines:
- Mention 3-5 key advantages of the recipe, e.g. diet friendliness (e.g. keto, high-protein), quick preparation, simple preparation, simple ingredients, healthy, etc.
- Use a casual, conversational tone as if you're talking to a friend
- Write at a 10th-grade English level - keep it simple and easy to understand
- Structure your section as a paragraph of 3-5 sentences
- Always begin the sentence with the advantage, as in the example provided down below
- Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
- Refrain from using strong adjectives

5. Your paragraph should mimic the style, tone, and sentence structure of this example (but not the content!):

JSON:
"
{
  "features": [
    {
      "feature": "Juicy, tender chicken breast",
      "description": "I won't have it any other way. And my tips will help you achieve just that. It was even good enough to make the cut for my first cookbook!"
    },
    {
      "feature": "Easy, flavorful pan sauce",
      "description": "Sure, you could sear chicken breast on both sides and call it a day, but it's so much better with my pan sauce. The garlicky, buttery white wine sauce all over the chicken makes it irresistible."
    },
    {
      "feature": "Simple ingredients",
      "description": "These are common staples I usually have around, and you probably do, too."
    },
    {
      "feature": "Quick and easy",
      "description": "This dish takes less than 30 minutes from start to finish. And it's faster than baking chicken breast!"
    },
    {
      "feature": "Healthy weeknight dinner",
      "description": "And it's naturally gluten-free. I usually make pan seared chicken breast for casual meals, but it can also work for special occasions."
    }
  ]
}
"

6. Format your output as follows:
- Put the headline "Why You'll Love This [dish]" inside <h2> tags
- Place the json after the headline, without any other content

Your output should be structured like this:
<h2>Why You'll Love This [dish]</h2>
{json output here}


Now, let's generate the section for the following recipe:

1. The recipe name is provided in the following tags:\n\n<recipe_name>\nEasy Egg Hashbrown Casserole\n</recipe_name>\n\n2. The ingredient list for the recipe is provided in the following tags:\n\n<ingredient_list>\n2 pounds thawed frozen hash brown potatoes\n1 pound pork sausage\n1 small diced onion\n5 eggs\n1/2 cup milk\n1/2 teaspoon onion powder\n1/8 teaspoon garlic powder\nSalt to taste\nBlack pepper to taste\n12 ounces shredded cheddar cheese\n</ingredient_list>"


Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. Use the recipe name and ingredient list to inform your suggestions about substitutions.
"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "The recipe name is:\n<recipe_name>\nWholesome Crockpot Beef Stew\n</recipe_name>\n\nThe ingredient list for this recipe is:\n\n<ingredient_list>\n2 ½ pounds of stew meat\n½ teaspoon each of black pepper, garlic salt, and celery salt\n1/4 cup flour\n3-6 tablespoons olive oil\n3 tablespoons chilled butter (split)\n2 cups chopped yellow onions\n4 minced garlic cloves\n1 cup cabernet sauvignon or merlot wine\n4 cups beef stock\n2 beef bouillon cubes\n2 tablespoons worcestershire sauce\n3 tablespoons tomato concentrate\n5 medium carrots, chopped into 1-inch pieces\n1 pound baby yukon gold potatoes, halved or quartered\n2 bay leaves\n1 rosemary sprig\n1 cup frozen peas\n1/4 cup cold water mixed with 3 tablespoons corn starch (optional)\n2-3 drops gravy master (optional for a deeper color)\n</ingredient_list>"
                        }
                    ]
                },
                {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": """<h2>Why You'll Love This Beef Stew</h2>
{
  "features": [
    {
      "feature": "Hands-off cooking",
      "description": "This crockpot beef stew practically makes itself while you go about your day, letting you come home to a warm, comforting meal."
    },
    {
      "feature": "Simple preparation",
      "description": "Just brown the meat, add your ingredients to the slow cooker, and let it do all the work for you."
    },
    {
      "feature": "Family-friendly comfort food",
      "description": "The tender beef, potatoes, and carrots swimming in rich gravy make this a crowd-pleasing dinner that even picky eaters will enjoy."
    },
    {
      "feature": "Budget-friendly",
      "description": "Using affordable stew meat and basic vegetables, this recipe transforms simple ingredients into a hearty meal that can feed a whole family with possible leftovers for lunch the next day."
    }
  ]
}"""
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nTotal Prep & Cooking Time: {time}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text

    except Exception as e:
        print(f"ERROR: {e}")
    
    html_section ='<div class="love">\n'
    # Parse JSON content if section contains features
    if '"features":' in section:
        try:
            # Extract h2 title
            h2_end = section.find('\n{')
            title = section[:h2_end]
            
            # Parse JSON
            json_str = section[h2_end:]
            features = json.loads(json_str)
            
            # Build HTML
            html_section += f"{title}\n"
            html_section += "<ul class='feature-list'>\n"
            
            for feature in features['features']:
                html_section += f"<li><strong>{feature['feature']}</strong> - {feature['description']}</li>\n"
                
            html_section += "</ul>\n"
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            html_section += f"{section}\n"
    else:
        html_section += f"{section}\n"
        
    html_section += "</div>\n<div class=\"hr--handdrawn\"></div>\n"

    return html_section

@backoff.on_exception(backoff.expo, anthropic.APIError,  max_time=300)
def generate_mistakes_section(title, ingredients):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational section for a recipe blog article. Your goal is to create a casual, easy-to-understand paragraph about for what to watch out wile cooking for the following recipe:

1. The recipe name is:
<recipe_name>

</recipe_name>

2. The ingredient list for this recipe is:
<ingredient_list>

</ingredient_list>

3. Write a paragraph about why you will love the recipe by following these guidelines:
- Mention 3-5 key mistakes to avoid while cooking the recipe. Also give practial and specific tips how to make it even better.
- Use a casual, conversational tone as if you're talking to a friend
- Write at a 10th-grade English level - keep it simple and easy to understand
- Structure your section as a paragraph of 3-5 sentences
- Always begin the sentence with the advantage, as in the example provided down below
- Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
- Refrain from using strong adjectives

4. Your paragraph should mimic the style, tone, and sentence structure of this example (but not the content!):

"The dry, tough reputation of boneless, skinless chicken breasts is due to one main factor: overcooking. How can you avoid making this fatal mistake?

Since chicken breasts are a lean cut, once they reach the safe temperature of 165°F they're already on the way to overcooking and drying out. Therefore, it's best to remove the chicken once an instant-read thermometer reaches 155°F when inserted into the thickest part of the breast. 

The residual heat will continue to cook the chicken breasts once they're out of the oven, bringing them up to temperature while keeping them moist and juicy."

5. Format your output as follows:
- Put the headline "Watch Out for These Mistakes While Cooking/Baking/Grilling" inside <h2> tags

- Place the paragraph immediately after the headline, without any additional tags

Your output should be structured like this:
<h2>Watch Out for These Mistakes While Cooking/Baking/Grilling</h2>
[Your 3-5 sentence paragraph goes here]

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. Use the recipe name and ingredient list to inform your suggestions about substitutions.
"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0.5,
            system=SYSTEM_PROMPT,
            messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "1. The recipe name is:\n<recipe_name>\nBlueberry French Toast Casserole\n</recipe_name>\n\n2. The ingredient list for this recipe is:\n<ingredient_list>\n1 pack (8 ounces) softened cream cheese\n1 cup powdered sugar\n2 tablespoons milk\n1 tablespoon vanilla extract, split\n2 cups blueberries, divided\n2 loaves cubed french bread\n2 cups milk\n8 eggs\n1 teaspoon cinnamon powder\n1/2 teaspoon ground nutmeg\n</ingredient_list>"
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "<h2>Watch Out for These Mistakes While Baking</h2>\nThe most common pitfall when making French toast casserole is using fresh bread, which can turn your breakfast into a soggy mess - day-old or slightly stale bread works best since it soaks up the custard mixture without falling apart. \n\nAnother key mistake is not letting the casserole rest for at least 30 minutes before baking (or better yet, overnight), as this time allows the bread to fully absorb the egg mixture and results in a more even texture. \n\nTo prevent your blueberries from sinking to the bottom, try tossing them in a little flour before adding them to the casserole, and don't forget to check the center with a knife before removing from the oven - it should come out clean, not wet. \n\nFor the best results, let the casserole rest for 10-15 minutes after baking, which helps it set properly and makes serving much easier."
                    }
                ]
            },
            {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                                }
                            ]
                        }
                    ]
                )

        section = message.content[0].text
    except Exception as e:
        print(f"ERROR: {e}")

    html_section= ""
    html_section += f"{section}\n"
    html_section += "<div class=\"hr--handdrawn\"></div>\n"

    return html_section

@backoff.on_exception(backoff.expo, anthropic.APIError,  max_time=300)
def generate_faq_section(title, ingredients):

    # Construct the prompt for the Claude model
    SYSTEM_PROMPT="""
You are a food blogger tasked with writing an informational FAQ section with 3 questions for a recipe blog article for the following recipe:

1. The recipe name is:
<recipe_name>

</recipe_name>

2. The ingredient list for this recipe is:
<ingredient_list>

</ingredient_list>

3. Questions: 

Think of 3 specific questions a recipe reader might ask themselves when making this recipe. 

NEVER use questions with the following topics because we're already covering them: 
- Storage, Freezing, Make Ahead, Reheat etc.
- Ingredient Substitutions (can I use x instead of y? etc.)
- Cooking Mistakes
- What kind of main ingredient to use
- When is the dish done
- What to serve with the dish 
- Do not use the question "Can I make x ahead of time?"



4. Write the FAQ section by following these guidelines:
- Use a casual, conversational tone as if you're talking to a friend. Be personal and write in first-person.
- Write at a 10th-grade English level - keep it simple and easy to understand
- Answer with "Yes" or "No" at the beginning of the sentence, if the question is a Yes/No question.
- Avoid using the following words: ultimate, stunning, vibrant, enhance, transform, admired, versatile, delicate, breathtaking, captivating
- Refrain from using strong adjectives

5. Your paragraph should mimic the style, tone, and sentence structure of this example (but not the content!):

"Are Banana Nut Muffins Keto?
With flour, sugar, and bananas, regular banana muffins are high in carbs and definitely not keto.

But this keto banana muffin recipe is keto friendly! They are low carb (just 4 grams net carbs), sugar-free, and packed with nutrients.

Are Banana Muffins Healthy?
Yes, this low carb banana muffin recipe is healthy! While many traditional banana muffins are made with white flour and sugar, these easy keto banana bread muffins are made with wholesome almond flour and allulose.


Can You Use Coconut Flour For This Recipe?
No, I don't recommend coconut flour for this recipe. They would turn out very dry and you'd need multiple other modifications.

If you can't have almonds, you'd be better off tweaking this coconut flour muffin recipe to remove the blueberries and add banana extract.

Can You Use Almond Meal?
No, I don't recommend using almond meal. You need blanched almond flour like this one. Using almond meal would result in a more grainy, cornmeal-like texture.


Can You Use A Different Sweetener?
No, you can use any granulated sweetener, but the result will be different. Allulose and monk fruit sweetener with allulose are the only two sweeteners that will make banana muffins with almond flour super moist. (Reduce the amount to 1/3 cup if you're using the monk fruit with allulose instead of pure allulose and want to keep these mildly sweet, or keep it at 1/2 cup for sweeter muffins.)


Other sweeteners can be used, the muffins just won't be as moist. If you want to use something else, use the keto sweetener conversion calculator to check the amount."

6. Format your output as follows:
- Combine the headline from the recipe name and "FAQ" and put the headline in <h2> tags, e.g. "<h2>Thumbprint Cookies FAQ</h2>"
- Put the question in <h3> tags
- Place the paragraph immediately after the headline, without any additional tags

Your output should be structured like this:
<h2>[dish here] FAQ</h2>
<h3>question 1</h3>
[Your 2-3 sentence paragraph goes here]

<h3>question 2</h3>
[Your 2-3 sentence paragraph goes here]

<h3>question 3</h3>
[Your 2-3 sentence paragraph goes here]

Remember to maintain a friendly, conversational tone throughout your writing, as if you're giving advice to a friend about cooking. 

Be personal and write in first-person. Use the recipe name and ingredient list to provide helpful questions.
"""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=600,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "1. The recipe name is:\n<recipe_name>\Easy Christmas Peppermint Oreo Cookies\n</recipe_name>\n\n2. The ingredient list for this recipe is:\n<ingredient_list>\n1 cup cold, cubed salted butter\n1 cup light brown sugar\n1/2 cup white sugar\n2 large eggs\n2 teaspoons vanilla essence\n3 cups all-purpose flour (423g)\n2 teaspoons cornstarch\n1 teaspoon baking soda\n3/4 teaspoon salt\n10-ounce package of andes peppermint crunch pieces\n1 1/2 cups coarsely crushed oreo cookies\n1/2 cup semisweet chocolate chips\n</ingredient_list>\n\n"
                            }
                        ]
                    },
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "text",
                                "text": "<h2>Peppermint Oreo Cookies FAQ</h2>\n\n<h3>Why do I need to use cold butter instead of room temperature butter?</h3>\nCold butter is key for these cookies because it creates a better texture. When cold butter is mixed into the dough, it creates small pockets that melt during baking, giving you cookies that are thick and chewy rather than flat and crispy. I always cube my butter first, then pop it back in the fridge until I'm ready to use it.\n\n<h3>Do I need to chill the cookie dough?</h3>\nYes, chilling the dough for at least 2 hours is really important for these cookies. The cold dough helps prevent the cookies from spreading too much in the oven, and it also gives the flour time to hydrate, which leads to better flavor. I know it's tempting to skip this step, but trust me - it's worth the wait!\n\n<h3>Should I crush the Oreos by hand or use a food processor?</h3>\nI recommend crushing the Oreos by hand rather than using a food processor. When you crush them by hand (I usually put them in a zip-top bag and use a rolling pin), you get nice chunky pieces that create perfect pockets of Oreo throughout the cookies. A food processor might make them too fine and powdery, which isn't what we're going for here."
                            }
                        ]
                    },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Recipe Name: {title}\n\nIngredients:\n{ingredients}\n"
                        }
                    ]
                }
            ]
        )

        section = message.content[0].text
        html_section=''
    except Exception as e:
        print(f"ERROR: {e}")
        
        # Parse JSON content if section contains ingredients
    
    
    html_section += f"{section}\n"
        
    html_section += "<div class=\"hr--handdrawn\"></div>\n"

    return html_section


def format_recipe_text(section):
    # Signalwörter für neue Absätze
    TRANSITION_PHRASES = [
        "Instead of",
        "you can use",
        "can be replaced",
        "if you don't have",
        "alternatively",
        "For the",
        "When it comes to",
        "As for"
    ]
    
    # Text in Sätze aufteilen
    # Wir behalten Punkte bei und strippen Whitespace
    sentences = [s.strip() for s in section.split('.') if s.strip()]
    
    formatted_text = ""
    
    for sentence in sentences:
        # Prüfe ob dieser Satz mit einer unserer Phrasen beginnt
        # oder ob eine Phrase im Satz vorkommt
        needs_paragraph = any(phrase.lower() in sentence.lower() for phrase in TRANSITION_PHRASES)
        
        # Wenn ja, fügen wir einen Absatz davor ein
        if needs_paragraph and formatted_text:
            formatted_text += "\n\n"
            
        # Satz hinzufügen (mit Punkt am Ende)
        formatted_text += sentence + "."
    
    return formatted_text

def htmlsteps(steps):
    """
    Writes HTML Steps with h2.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
    {
        "role": "system",
        "content": "You are a pro at writing recipes. \nYou use basic US English. \nThe focus is always on reader-friendliness and usability. \nYour task is to structure the recipe well and group the single steps into 3-6 work steps that are absolutely sensible for the user. \nDo not give me a list of ingredients. Only reply with the steps.\nPlease output the text in HTML format.\nAlways begin the headline with \"Step 1:\", \"Step 2:\"..."
    },
    {
        "role": "user",
        "content": "Please write a recipe for my blog article for the topic \"Cottage Cheese Alfredo Sauce | High Protein & Creamy\". \n\nPlease use the following steps to create the recipe:\n\n1. Add 1 and 1/2 cups of cottage cheese, half a cup of milk, 1 and 1/2 teaspoons of Italian seasoning, half a cup of grated Parmesan cheese, half a teaspoon of black pepper, and a pinch of salt to a blender or food processor.\n2. Blend everything together until smooth.\n3. If the mixture is too thick, add a little more milk or some higher protein bone broth.\n4. Take out a stove top pan and turn the burner on low heat, then add in 1 and 1/2 tablespoons of butter.\n5. Once the butter melts, add in a tablespoon of minced garlic and let it cook for a few minutes.\n6. Pour in the cottage cheese mixture and a teaspoon of corn starch, and keep stirring often as everything heats up and begins to thicken.\n7. Cook on low heat, as high heat can ruin the sauce.\n8. While the sauce is heating up, cook some pasta according to the package instructions.\n9. Once the pasta is done, drain it and add it to the Alfredo sauce.\n10. Mix everything around for a couple of minutes, then add in any additional ingredients you like (such as cooked protein or crushed red pepper).\n11. Serve hot, and reheat as needed by mixing in a little milk and reheating over low heat.\n\nPlease output a text divided into several steps that are marked as h2 header. \nGroup the single steps into meaningful headlines. \nDo not give me a list of ingredients. Only reply with the steps.\nPlease output the text in html format."
    },
    {
        "role": "assistant",
        "content": "<h2>Step 1: Blend the Cottage Cheese Mixture</h2>\n<p>Start by adding 1 and 1/2 cups of cottage cheese, half a cup of milk, 1 and 1/2 teaspoons of Italian seasoning, half a cup of grated Parmesan cheese, half a teaspoon of black pepper, and a pinch of salt into a blender or food processor. Blend until the mixture becomes smooth and creamy. If the mixture seems too thick, you can adjust the consistency by adding a bit more milk or some higher protein bone broth.</p>\n\n<h2>Step 2: Prepare the Garlic Butter</h2>\n<p>Place a stovetop pan over low heat and melt 1 and 1/2 tablespoons of butter in it. Once the butter is melted, add a tablespoon of minced garlic and let it cook for a few minutes until fragrant. Be careful not to burn the garlic.</p>\n\n<h2>Step 3: Combine and Heat the Sauce</h2>\n<p>Pour the blended cottage cheese mixture into the pan with the garlic butter. Add a teaspoon of corn starch, then stir continuously as the sauce begins to heat and thicken. Maintain the heat at a low setting to prevent the sauce from curdling or separating.</p>\n\n<h2>Step 4: Cook the Pasta</h2>\n<p>As the sauce is warming up, cook your favorite pasta according to the package instructions. Once the pasta is al dente, drain it well and immediately add it to the pan with the Alfredo sauce. Stir everything together to ensure the pasta is evenly coated with the creamy sauce.</p>\n\n<h2>Step 5: Final Touches and Serve</h2>\n<p>If you want to add extra flavor or protein, incorporate any additional ingredients like cooked chicken, shrimp, or a sprinkle of crushed red pepper at this stage. Mix everything thoroughly and serve hot. If the sauce thickens too much upon reheating, simply add a splash of milk and reheat over low heat until smooth again.</p>"
    },
    {
        "role": "user",
        "content": "1. Get a large measuring cup or a medium-sized bowl and place it on a food scale.\n2. Measure out 42 grams (less than 1/3 cup) of almond flour into the bowl.\n3. Add 1/4 teaspoon of baking powder to the bowl.\n4. Add 1/4 teaspoon of xanthan gum (or guar gum as a substitute) to the bowl.\n5. Add a pinch of salt to the bowl.\n6. Add some garlic powder and onion powder to the bowl for flavor.\n7. Add 2 tablespoons (22 grams) of water to the bowl and mix until a thick, sticky dough forms.\n8. Coat an 8-ounce ramekin with baking spray.\n9. Add the dough to the ramekin and spread it out evenly using a spatula coated with water.\n10. Microwave the pizza dough for 1 minute or bake in the oven at 350\u00b0F (175\u00b0C) for 20 minutes.\n11. Remove the pizza crust from the microwave or oven and add 2 tablespoons (30 grams) of pizza sauce.\n12. Add less than a quarter cup (21 grams) of full-fat mozzarella cheese on top of the pizza sauce.\n13. Add mini slices of pepperoni on top of the cheese.\n14. Microwave the pizza for 30 seconds on the left side, then 30 seconds on the right side, or broil in the oven for a few minutes until the cheese melts."
    },
    {
        "role": "assistant",
        "content": "<h2>Step 1: Measure and Combine Dry Ingredients</h2>\n<p>Begin by getting a large measuring cup or a medium-sized bowl and placing it on a food scale. Measure out 42 grams (less than 1/3 cup) of almond flour into the bowl. Add 1/4 teaspoon of baking powder, 1/4 teaspoon of xanthan gum (or guar gum as a substitute), a pinch of salt, and some garlic powder and onion powder for flavor. Mix these dry ingredients together thoroughly.</p>\n\n<h2>Step 2: Add Water and Form the Dough</h2>\n<p>To the bowl of combined dry ingredients, add 2 tablespoons (22 grams) of water. Mix until a thick, sticky dough forms. This may take a little bit of effort to ensure all the dry ingredients are fully integrated into the water.</p>\n\n<h2>Step 3: Prepare the Ramekin and Spread the Dough</h2>\n<p>Coat an 8-ounce ramekin with baking spray to prevent the dough from sticking. Add the dough to the ramekin and spread it out evenly using a spatula coated with water to keep the dough from sticking to the spatula.</p>\n\n<h2>Step 4: Cook the Pizza Crust</h2>\n<p>Microwave the pizza dough for 1 minute, or alternatively, bake in the oven at 350\u00b0F (175\u00b0C) for 20 minutes until the crust is set and slightly golden. This will create a solid base for the toppings.</p>\n\n<h2>Step 5: Add Toppings and Melt the Cheese</h2>\n<p>Remove the pizza crust from the microwave or oven. Spread 2 tablespoons (30 grams) of pizza sauce over the crust. Sprinkle less than a quarter cup (21 grams) of full-fat mozzarella cheese on top of the sauce. Add mini slices of pepperoni over the cheese. Microwave the pizza for 30 seconds on the left side, then 30 seconds on the right side, or broil in the oven for a few minutes until the cheese melts and becomes bubbly.</p>\n\n<h2>Step 6: Serve and Enjoy</h2>\n<p>Once the cheese has melted to your liking, remove the ramekin from the microwave or oven, being careful as it will be hot. Let the pizza cool for a minute before digging in. Enjoy your quick and delicious personal pizza!</p>"
    },
    {
        "role": "user",
        "content": steps
    }
]

    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stop=None
    )

    content = response.choices[0].message.content

   # Nachbearbeitung des Inhalts
    paragraphs = content.split('\n')
    formatted_paragraphs = []

    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():
            if re.match(r'<h[1-6]>', paragraph):
                # Füge einen Trenner vor jeder <h2>, außer vor der ersten
                if i > 0 and re.match(r'<h2>', paragraph):
                    formatted_paragraphs.append('<div class="hr--handdrawn"></div>')
                formatted_paragraphs.append(paragraph.strip())
            else:
                # Entfernen Sie zusätzliche Punkte am Ende der Sätze
                paragraph = re.sub(r'\.+', '.', paragraph)
                # Teilen Sie den Absatz in Sätze
                sentences = re.split(r'(?<=[.!?])\s+', paragraph.strip())
                # Fügen Sie jeden Satz als separaten Absatz hinzu
                formatted_paragraphs.extend(sentences)

    formatted_content = '\n\n'.join(formatted_paragraphs)

    return formatted_content

def htmlliste(ingr):
# Entferne den einleitenden Satz und leere Zeilen, ignoriere Groß-/Kleinschreibung
    ingredients = [
        line.strip() for line in ingr.split('\n')
        if line.strip() and not line.lower().startswith('here is')
    ]
    html_output = '<h2>Ingredients</h2>\n<ul class="ingr">\n' + ''.join(f'    <li>{ingredient.capitalize()}</li>\n' for ingredient in ingredients) + '</ul>\n<div class="hr--handdrawn"></div>'

    return html_output

def table(title, steps):
    """
    Creates JSON Prep Time and Converts into HTML Table.
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
    {
        "role": "system",
        "content": "Please output in JSON format the following values:\n\nPreparation Time\nCooking Time\nTotal Time\nLevel of Difficulty\n\nFor the Level of Difficulty you have the range of Easy, Medium and Hard. \n\nAlways specify the output in minutes and in range minimum to maximum."
    },
    {
        "role": "user",
        "content": "Recipe Name: Cottage Cheese Alfredo Sauce Creamy & High Protein\n\nCalculate the values from the system prompt based on the following steps:\n\n1. Gather ingredients: 2 eggs and 1 cup of cottage cheese.\n2. Add flavorings (optional): up to 1 teaspoon of herbs or spices, such as garlic spread and chives.\n3. Blend eggs, cottage cheese, and flavorings in a blender or Thermomix until well combined.\n4. Prepare a 9x13 pan by lining it with parchment paper.\n5. Pour the dough onto the parchment paper and spread it out into a rectangle shape.\n6. Bake in a preheated oven at 375°F (190°C) for 2 hours, or at 350°F (175°C) for 2.5 hours.\n7. Remove from the oven and let cool.\n8. Use the flatbread to make sandwiches, wraps, or as a pizza crust.\n9. Store leftovers wrapped tightly in plastic or foil in the fridge, or freeze for later use.\n\nAnswer with JSON Output.\n"
    },
    {
        "role": "assistant",
        "content": "{\n\"Preparation Time\": \"15-30 minutes\",\n\"Cooking Time\": \"120-150 minutes\",\n\"Total Time\": \"135-180 minutes\",\n\"Level of Difficulty\": \"Easy\"\n}"
    },
    {
        "role": "user",
        "content": str(f"Recipe Name: {title}\n\nSteps:\n{steps}")
    }
    ]


    response = client.chat.completions.create(
        messages=messages,
        #model="llama3-70b-8192",
        model="gpt-4o-mini",
        temperature=1,
        max_tokens=200,
        top_p=1,
        response_format={"type": "json_object"}
        #stop=None
    )

    jdata = response.choices[0].message.content

    # JSON-Daten in ein Python-Wörterbuch umwandeln
    data = json.loads(jdata)

    # HTML-Tabellenanfang
    html_table = "<table>\n<tbody>\n"

    # Tabellenkopf und Datenzeilen hinzufügen
    html_table += "".join(f"<tr><td><b>{key}</b></td><td>{value}</td></tr>\n" for key, value in data.items())

    # HTML-Tabellenende
    html_table += '</tbody>\n</table>\n<div class="hr--handdrawn"></div>'
    # Total Zeit berechnen
    total_time = data.get("Total Time", "")
        # Ergebnis ausgeben
    return html_table, total_time

# Nutrition Estimate
def nutritionestimate(ingredients):
    """
    Creates JSON Nutrition and Converts into HTML Table.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "You are a nutrition expert tasked with estimating the nutritional content of a recipe based on its ingredient list. You will be provided with a list of ingredients and their amounts. Your goal is to estimate the nutritional values for the entire recipe and present them in a specific format.\n\nHere is the ingredient list for the recipe:\n<ingredient_list>\n{{INGREDIENT_LIST}}\n</ingredient_list>\n\nFollow these steps to complete the task:\n\n1. Carefully review the ingredient list, noting the ingredients and their quantities.\n\n2. Estimate the nutritional values for the entire recipe, focusing on these characteristics:\n   - Calories\n   - Protein\n   - Fat\n   - Carbohydrates\n\n3. For each nutritional characteristic, provide a range rather than a single value to account for estimation uncertainty. For example, \"Calories: 300-350\" instead of \"Calories: 325\".\n\n4. If there are any optional ingredients mentioned in the list, do not include them in your calculations. \n\n5. Present your estimated nutritional information in JSON format . Use the following structure:\n\n{\n  \"Calories\": \"X-Y\",\n  \"Protein\": \"A-B g\",\n  \"Fat\": \"C-D g\",\n  \"Carbohydrates\": \"E-F g\"\n}\n\n6. If there are no optional ingredients, omit the \"Note\" field from the JSON output. Only answer with the JSON output.\n\n7. If no quantities are specified, do not include them in the calculation, either.\n\nRemember, these are estimates based on the ingredient list provided. Actual nutritional values may vary depending on specific brands, preparation methods, and serving sizes."
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "{\n  \"Calories\": \"350-400\",\n  \"Protein\": \"30-35 g\",\n  \"Fat\": \"22-26 g\",\n  \"Carbohydrates\": \"5-8 g\"\n}"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "4 large whole eggs\n1/2 cup cottage cheese\nSalt\nBlack pepper\nOil or butter (for cooking)\nOptional seasonings (e.g., garlic powder)\nChopped vegetables (optional)\nGround beef or turkey (optional)\nBacon bits (optional)\nChopped chives (optional)"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "8 ounces penne pasta\n1/2 teaspoon sea salt (for boiling water)\n2 skinless, boneless chicken breasts (around 1 pound)\nPinch each of salt and pepper (for chicken seasoning)\n1 tablespoon olive oil (or your choice of cooking oil)\n1 medium onion (chopped)\n3 cloves garlic (chopped)\n1/4 cup vodka\n1 can (28 ounces) crushed tomatoes\n1/2 cup heavy cream\n1/4 cup fresh oregano (or 1 teaspoon dried)\n1/4 teaspoon red pepper flakes\n1/4 cup grated parmesan cheese (plus extra for garnish)\nSalt and pepper (to your preference)"
        }
      ]
    },
    {
      "role": "assistant",
      "content": [
        {
          "type": "text",
          "text": "{\n  \"Calories\": \"1400-1600\",\n  \"Protein\": \"80-90 g\",\n  \"Fat\": \"70-80 g\",\n  \"Carbohydrates\": \"110-120 g\"\n}"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": str(ingredients)
        }
      ]
    }
    ]


    response = client.chat.completions.create(
        messages=messages,
        model="gpt-4o-mini",
        temperature=1,
        max_tokens=200,
        top_p=1,
        response_format={"type": "json_object"},
        #stop=None
    )

    jdata = response.choices[0].message.content

    # JSON-Daten in ein Python-Wörterbuch umwandeln
    data = json.loads(jdata)

    # Füge die Überschrift und den Absatz hinzu
    html_output = f"<h2>Estimated Nutrition</h2>\n<p>Estimated nutrition for the whole recipe <i>(without optional ingredients)</i>:</p>\n"

    # Füge die ungeordnete Liste hinzu
    html_output += "<ul class='ingr'>\n"
    for key, value in data.items():
        html_output += f"<li><strong>{key}:</strong> {value}</li>\n"
    html_output += "</ul>\n"

    # Füge die handgezeichnete Linie hinzu
    html_output += '<div class="hr--handdrawn"></div>\n'

    # Ergebnis ausgeben
    return html_output


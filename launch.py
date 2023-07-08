import vertexai
from vertexai.language_models import TextGenerationModel
import whisper
import gradio as gr
from datetime import datetime

vertexai.init(project="bing-chillin-o81m8v", location="us-central1")
model = whisper.load_model("base")

lean_context = """As a data analyst at a supermarket, you have been given the task of writing SQL code to address business questions. You have several tables available for analysis:
  1. \"COMPANY.TABLES.SALES\" AS ISS: This table contains transaction data at the product-basket level, recording all supermarket transactions. Key columns include:
  TRANSACTION_DATE: Date of the transaction
  , STORE: Store code
  , PRODUCT: Product code
  , CHANNEL: Channel code (100 for online, 105 for in-store)
  , BASKET_ID: Unique identifier for each transaction basket
  , UNITS: Quantity of units sold
  , SALES: Total sales amount.
  2. \"COMPANY.TABLES.CUSTOMER_SALES\" AS IDX: This table records transactions where customers have scanned their loyalty cards. It contains data at the customer-product-basket level. Key columns are similar to the \"SALES\" table, with the addition of CUSTOMER_ID.
  3. \"COMPANY.TABLES.PRODUCTS\" AS PROD: This table provides information about products in the supermarket. Key columns include:
  PRODUCT: Unique product identifier
  , PRODUCT_NAME: Name of the product
  , SUBCATEGORY: Subcategory the product belongs to
  , SEGMENT: Segment the product belongs to
  , BRAND: Brand name
  SUPPLIER: Supplier or manufacturer name.
  4. \"COMPANY.TABLES.STORES\" AS STO: This table contains information about supermarket stores. Key columns include:
  STORE_ID: Unique store identifier
  , STORE_NAME: Store name
  , STATE: State where the store is located
  , STORE_CLUSTER: Store cluster (CORE, VALUE, or UP)
  , LOCALITY: Specific area within the state where the store is situated.
  5. \"COMPANY.TABLES.PROMOTIONS\" AS PET: This table contains information about promotions for supermarket products. Key columns include:
  PRODUCT: Product identifier
  , PROMOTION_WEEK: End date of the promotion week. Each promotion week starts on Wednesday and ends on the following Tuesday
  , PROMOTION_DEPTH: Depth or intensity of the promotion (0 to 1)
  , DISPLAY: Type of promotional display can be \"DISPLAY 1\" \"DISPLAY 2\" or \"NO DISPLAY\" for not promoted by display, 
  , MAGAZINE: Boolean indicating if the promotion is featured in a magazine (TRUE or FALSE).
  5. \"COMPANY.TABLES.AFFLUENCE_SEGMENTATION\" AS BMP: This table classifies customers into three affluence groups: BUDGET, MAINSTREAM, and PREMIUM. Key columns are CUSTOMER_ID and CUSTOMER_SEGMENT. Affluence CUSTOMER_SEGMENT can be  BUDGET, MAINSTREAM, or PREMIUM.
  6. \"COMPANY.TABLES.LIFESTAGE_SEGMENTATION\" AS LF: This table classifies customers into different life stage groups, such as New Families, Young Families, and Older Families. Key columns are CUSTOMER_ID and CUSTOMER_SEGMENT. Life stage CUSTOMER_SEGMENT can be New Families, Young Families, and Older Families.
  You can join these tables using the following conditions:
  1. \"SALES\" and \"PRODUCTS\" on the \"PRODUCT\" column.
  2. \"SALES\" and \"PROMOTIONS\" on the transaction date one day before the next Wednesday.
  3. \"SALES\" and \"STORES\" on the \"STORE_ID\" column.
  4. \"CUSTOMER_SALES\" and \"PRODUCTS\" on the \"PRODUCT\" column.
  5. \"CUSTOMER_SALES\" and \"STORES\" on the \"STORE_ID\" column.
  6. \"CUSTOMER_SALES\" and \"AFFLUENCE_SEGMENTATION\" on the \"CUSTOMER_ID\" column.
  7. \"CUSTOMER_SALES\" and \"LIFESTAGE_SEGMENTATION\" on the \"CUSTOMER_ID\" column.
  8. \"CUSTOMER_SALES\" and \"PROMOTIONS\" on the transaction date one day before the next Wednesday.
  """

examples = """
  input: For the week ending 25 December 2018, calculate the daily sales for the multipacks ice cream subcategory in the state of NSW that were discounted 50% or more.
  output: Of course, here is the SQL code that will find the daily sales for the Multipacks Ice Cream subcategory in the state of NSW at 50% or greater discount for the week ending 25 December 2018.
  The analysis plan is as follows:
  1. Inner join the COMPANY.TABLES.SALES table to the COMPANY.TABLES.PRODUCT table, the COMPANY.TABLES.STORES table, and the COMPANY.TABLES.PROMOTIONS table.
  2. Filter transaction dates to the week ending 25 December 2018.
  3. Filter to the Multipacks Ice Cream subcategory.
  4. Filter to the state of NSW.
  5. Filter to promotion depth greater than 0.5.
  6. Group by transaction date.
  7. Sum sales.
  ```sql
  SET END_DATE = DATE \'2018-12-25\';
  CREATE OR REPLACE TABLE COMPANY.QUERIES.USER_QUERY AS (
    SELECT TRANSACTION_DATE
      ,SUM(SALES) AS TOTAL_SALES 
    FROM COMPANY.TABLES.SALES AS ISS
    INNER JOIN COMPANY.TABLES.PRODUCTS AS PROD
    ON ISS.PROD_NBR = PROD.PROD_NBR
    INNER JOIN COMPANY.TABLES.STORES AS STO
    ON ISS.STORE_ID = STO.STORE_ID
    INNER JOIN COMPANY.TABLES.PROMOTIONS AS PET
    ON ISS.PROD_NBR = PET.PROD_NBR
    AND NEXT_DAY(ISS.TRANSACTION_DATE, \'WED\') - 1 = PET.PROMOTION_WEEK
    WHERE PROMOTION_WEEK = $END_DATE
    AND PROD.SUBCATEGORY = \'MULTIPACKS ICE CREAM\'
    AND STO.STATE = \'NSW\'
    AND PET.PROMOTION_DEPTH >= 0.5
    GROUP BY TRANSACTION_DATE
  );
  ```
  input: What is the weekly sales and units sold for the Bulla Fudge bars product during the last 11 weeks when promoted on display 2 in the Punchbowl store?
  output: No problem, below is the SQL code that will find the weekly sales and units sold for the Bulla Fudge Bars product on promotion on display 2 in the Punchbowl store for the last 11 weeks.
  Please see the analysis plan:
  1. Inner join the COMPANY.TABLES.SALES table to the COMPANY.TABLES.PRODUCT table, the COMPANY.TABLES.STORES table, and the COMPANY.TABLES.PROMOTIONS table.
  2. Filter transaction dates to the latest available 11 weeks.
  3. Filter to the Bulla Fudge Bars product.
  4. Filter to the Punchbowl store.
  5. Filter to display 2.
  6. Group by week.
  7. Sum sales.
  ```sql
  SET END_DATE = DATE \'2022-12-12\';
  CREATE OR REPLACE TABLE COMPANY.QUERIES.USER_QUERY AS (
    SELECT NEXT_DAY(ISS.TRANSACTION_DATE, \'WED\') - 1 AS WEEK_END_DATE
      ,SUM(SALES) AS TOTAL_SALES 
      ,SUM(UNITS) AS TOTAL_UNITS
    FROM COMPANY.TABLES.SALES AS ISS
    INNER JOIN COMPANY.TABLES.PRODUCTS AS PROD
    ON ISS.PROD_NBR = PROD.PROD_NBR
    INNER JOIN COMPANY.TABLES.STORES AS STO
    ON ISS.STORE_ID = STO.STORE_ID
    INNER JOIN COMPANY.TABLES.PROMOTIONS AS PET
    ON ISS.PROD_NBR = PET.PROD_NBR
    AND NEXT_DAY(ISS.TRANSACTION_DATE, \'WED\') - 1 = PET.PROMOTION_WEEK
    WHERE ISS.TRANSACTION_DATE BETWEEN $END_DATE - 11*7 + 1 AND $END_DATE
    AND PROD.PRODUCT_NAME = \'BULLA FUDGE BARS\'
    AND STO.STORE_NAME = \'PUNCHBOWL\'
    AND PET.DISPLAY = \'DISPLAY 2\'
    GROUP BY WEEK_END_DATE
  );
  ```
  """

def bing(prompt):
  parameters = {
      "temperature": 0.5,
      "max_output_tokens": 1024,
      "top_p": 1,
      "top_k": 40
  }
  model = TextGenerationModel.from_pretrained("text-bison")
  curr_date = "The current date is \'" + str(datetime.today().strftime('%Y-%m-%d')) + "\'"
  full_context = lean_context + curr_date + examples
  response = model.predict(full_context + "input: " + prompt + "output:", **parameters)

  return response.text
  
def inference(audio):
    audio = whisper.load_audio(audio)
    audio = whisper.pad_or_trim(audio)
    
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    
    _, probs = model.detect_language(mel)
    
    options = whisper.DecodingOptions(fp16 = False)
    result = whisper.decode(model, mel, options)
    
    return result.text

def chillin(input, history):
    history = history or []
    s = list(sum(history, ()))
    s.append(input)
    inp = ' '.join(s)
    output = bing(inp)
    history.append((input, output))
    return history, history

def chillin_audio(input, history):
    history = history or []
    s = list(sum(history, ()))
    input_text = inference(input)
    s.append(input_text)
    inp = ' '.join(s)
    output = bing(inp)
    history.append((input_text, output))
    return history, history

with gr.Blocks() as block:
    gr.Markdown("""<h1><center>Bingchillin X Quantium</center></h1>""")
    chatbot = gr.Chatbot()
    state = gr.State()

    speech = gr.inputs.Audio(source="microphone", type="filepath")
    submit1 = gr.Button("吃了")
    submit1.click(chillin_audio, inputs=[speech, state], outputs=[chatbot, state])

    message = gr.Textbox(placeholder="吃了吗?")
    submit2 = gr.Button("吃了")
    submit2.click(chillin, inputs=[message, state], outputs=[chatbot, state])
    
block.launch(inline = False)

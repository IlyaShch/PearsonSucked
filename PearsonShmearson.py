# Currently assumes you left your pearson textbook navigated to a chapter you want to complete.
# Its not pretty but gets the job done.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
from openai import OpenAI
import requests
import pyperclip
import selenium.common.exceptions as selExcept

def load_config(file_path="config.json"):
    with open(file_path, "r") as file:
        config = json.load(file)
    return config

# Read and display credentials
config = load_config("credentials.json")

password=config['pearson_password']
username =config['pearson_username']
cmscAssgnmentConsole=config['course_console_URL']



######### CHAT GPT SETUP HEADER #############
openai_api_key=config['chatgpt_api_key']
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
}

#completions api entrypoint
url = "https://api.openai.com/v1/chat/completions"

##############FUNCTIONS##################

#Sends chatGPT a single question 
#Returns a solution text.
def gptSolve(request):
        
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a Programming homework solving machine. All output must be C++ code. Output just the solution to the question. Make sure to only do what is instructed in the question. Remove the ```cpp formatting from the text."
            },
            {
                "role": "user",
                "content": request
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    return response.json()['choices'][0]['message']['content']

#Solves a single question in a quiz
def solveQuestion(iframe):

    # Tring to get Assingment text, reloading in case page bugs
    # The output is ultimately a variable called "problem"
    try:
        div_element = driver.find_element(By.CLASS_NAME, "inner-markdown-viewer")
        problem = div_element.text
    except Exception as e:
        driver.refresh()
        time.sleep(1)
        div_element = driver.find_element(By.CLASS_NAME, "inner-markdown-viewer")
        problem = div_element.text

    #Calls to solve the problem
    solution= gptSolve(problem)
    
    #Try statement checking for multiple choice question variant.
    try:
        editor = driver.find_element(By.CSS_SELECTOR, "textarea.inputarea")
             
        # Clear existing content 
        editor.send_keys(Keys.CONTROL + "a")  # Select all
        editor.send_keys(Keys.BACKSPACE)  # Delete selected content

        #Copy pastes in solution to avoid bracket issues
        pyperclip.copy(solution)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("v").key_up(Keys.CONTROL).perform()
    except selExcept.NoSuchElementException as e:
        print("Probably Multiple Choice")
    
    return

#solution for a single quiz instance
def solveQuiz(e):
    
    #open quiz
    driver.execute_script("arguments[0].click();", e)


    #open the assessment
    button = driver.find_element(By.ID, "btnViewAssessment")
    driver.execute_script("arguments[0].click();", button)

    #Switch to the quiz frame
    iframe = driver.find_element(By.CLASS_NAME, "link-iframe")
    driver.switch_to.frame(iframe)

    solveQuestion(iframe)

    # Locate the button by aria-label
    try:
        button = driver.find_element(By.XPATH, '//button[@aria-label="Next Question"]')

        while(button.get_attribute("disabled")!="true"):
            button.click()
            button = driver.find_element(By.XPATH, '//button[@aria-label="Next Question"]')
            solveQuestion(iframe)
            print(button.get_attribute("disabled"))
    except Exception as e:
        print("No next button")


    # Auto submission still needs work. It's not finding the submit button. 
    # Im out of test projects till next week though ;)
    # try:
    #     button = driver.find_element(By.ID, "submit-button-2")
    #     # Click the button
    #     button.click()
    # except selExcept.NoSuchElementException as e:
    #     print("Couldnt Submit")


    #exit iframe
    driver.switch_to.default_content()
    
    #Finding a way to select this was a pain but it has tab index 0 
    actions = ActionChains(driver)
    actions.send_keys(Keys.TAB).send_keys(Keys.ENTER).perform()
    
    return 




driver = webdriver.Chrome()
driver.implicitly_wait(3)

# logging into the main pearson website
pearson="https://login.pearson.com/v1/piapi/piui/signin?client_id=dN4bOBG0sGO9c9HADrifwQeqma5vjREy"
driver.get(pearson)

#a valid login, however tends to redirect to a real page after??
#this could definitely be condensed into less repetitve code
usernameElement=driver.find_element(By.ID, "username")
usernameElement.send_keys(username)
passwordElement=driver.find_element(By.ID, "password")
passwordElement.send_keys(password)
driver.find_element(By.ID, "onetrust-button-group").click()
login=driver.find_element(By.ID, "mainButton")
driver.execute_script("arguments[0].click();", login)

time.sleep(3)

usernameElement=driver.find_element(By.ID, "username")
usernameElement.send_keys(username)
passwordElement=driver.find_element(By.ID, "password")
passwordElement.send_keys(password)

login=driver.find_element(By.ID, "mainButton")
driver.execute_script("arguments[0].click();", login) #This felt super useful. Waits for stuff to be loaded before clicking


#Redirect to actual page.
loadedTrigger=driver.find_element(By.CLASS_NAME,"page-title" )
EC.presence_of_element_located(loadedTrigger)

#login to the assingment console
driver.get(cmscAssgnmentConsole)

time.sleep(1)


#Navigate to the textbook
try:
    button = driver.find_element(By.XPATH, "//button[.//div[text()='Continue reading']]")
    driver.execute_script("arguments[0].click();", button)
except Exception as e:
    driver.refresh()
    time.sleep(1)
    button = driver.find_element(By.XPATH, "//button[.//div[text()='Continue reading']]")
    driver.execute_script("arguments[0].click();", button)




# isEmpty = driver.find_elements(By.XPATH, "//div[@class='emptyMessage']/span[contains(text(), 'Sorry, we could not complete your request')]")
# if isEmpty:
#     driver.refresh()

#List of quizzes in chapter
elements = driver.find_elements(By.XPATH, "//span[starts-with(text(), 'Quiz')]")

for e in elements:
    print(e)
    solveQuiz(e)


input("No way! Youre done with this chapters HW!")
driver.close()





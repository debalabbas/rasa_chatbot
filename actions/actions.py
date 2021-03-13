#This files contains your custom actions which can be used to run
#custom Python code.

#See this guide on how to implement these action:
#https://rasa.com/docs/rasa/custom-actions


#This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import random as rnd
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class ActionCheckWeather(Action):

    def name(self) -> Text:
        return "action_check_weather"

    @staticmethod
    def city_forecast(city):
        response = requests.get(
            "https://community-open-weather-map.p.rapidapi.com/forecast?q=" + city,
            headers={
                "X-RapidAPI-Host": "community-open-weather-map.p.rapidapi.com",
                'x-rapidapi-key': "45785b16d4msh04af1fb94f8a16bp16cff1jsn8d7dcfb0bd4b"
            },
        )
        return response.json()

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        entity = next(tracker.get_latest_entity_values('topic_news'), 'not found')
        if entity:
            location = entity
        else:
            location = tracker.get_slot('location')
            if not location:
                dispatcher.utter_message("Sorry I don't know your location")
                return []
        details = self.city_forecast(city=location)
        temperature = details['list'][0]['main']['temp'] - 273.15
        min_temperature = details['list'][0]['main']['temp_min'] - 273.15
        max_temperature = details['list'][0]['main']['temp_max'] - 273.15
        description = details['list'][0]['weather'][0]['description']

        dispatcher.utter_message(f"Weather forecast for {location} is:\n"
                                 f"Minimum Temperature: {round(min_temperature,2)} degree celcius\n"
                                 f"Maximum Temperature: {round(max_temperature,2)} degree celcius\n"
                                 f"Description: {description.title()}\n"
                                 f"The temperature now is {round(temperature,2)} degree celcius")

        if entity:
            return []
        else:
            return SlotSet("location", location)


class ActionResetSlot(Action):

    def name(self) -> Text:

        return "action_reset_slot"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet('location', None)]


class ActionTellJoke(Action):

    def name(self) -> Text:
        return "action_tell_joke"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        category = rnd.choice(['Dark', 'Programming', 'Misc', 'Pun'])
        url = "https://jokeapi-v2.p.rapidapi.com/joke/" + category

        type_of_joke = rnd.choice(['single', 'twopart'])

        querystring = {"format": "json", "blacklistFlags": "nsfw,racist,sexist,explicit", "idRange": "0-150",
                       "type": type_of_joke}

        headers = {
            'x-rapidapi-key': "45785b16d4msh04af1fb94f8a16bp16cff1jsn8d7dcfb0bd4b",
            'x-rapidapi-host': "jokeapi-v2.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        if type_of_joke == 'single':
            joke = response.json()['joke']

        else:
            joke = response.json()['setup'] + response.json()['delivery']

        dispatcher.utter_message(joke)

        return []


class ActionTellNews(Action):

    def name(self) -> Text:
        return "action_tell_news"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        category = next(tracker.get_latest_entity_values('news_category'), None)
        topic = next(tracker.get_latest_entity_values('topic_news'), None)
        print('check')
        if not(category and topic):
            category = 'general'
            print('check')

        url = 'https://newsapi.org/v2/top-headlines?'
        headers = {'X-Api-Key': '9434dcd25558404db9d3ecbda4db0d65'}
        params = {'country': 'in', 'category': category, 'q': topic}
        response = requests.request('GET', url, headers=headers, params=params)
        print('check')
        if response.json()['articles']:
            dispatcher.utter_message("I hope this helps you")
            for x in response.json()['articles'][:5]:
                try:
                    dispatcher.utter_message(text=x['title'], image=x['urlToImage'],attachment=x['url'])
                except:
                    pass
        else:
            dispatcher.utter_message('Sorry no news articles exist for your particular search')
        return []


class ActionSendSMS(Action):

    def name(self) -> Text:
        return "action_send_sms"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        account_sid = 'AC5155dddcdc7c335acc49437cdb61c9d2'
        auth_token = 'eb3b0dd0ec1a45740e441403d070f90e'
        client = Client(account_sid, auth_token)

        reciever = tracker.get_slot('to_number')
        content = tracker.get_slot('content')
        message = client.messages.create(
            messaging_service_sid='MG7f8ef3ef49ac13b33c80525539c1591e',
            body=content,
            to=reciever
        )

        print(message.sid)

        dispatcher.utter_message(f'Message sent to {reciever}')

        return [SlotSet('to_number', None), SlotSet('content', None)]


class ActionSendMail(Action):

    def name(self) -> Text:
        return "action_send_mail"

    @staticmethod
    def send_mail(reciever_addr, sub, body):

        sender_addr = 'debalcena.247@gmail.com'
        msg = MIMEMultipart()
        flag = 1

        msg['From'] = sender_addr
        msg['To'] = reciever_addr
        msg['Subject'] = sub

        msg.attach(MIMEText(body,'plain'))

        s = smtplib.SMTP('smtp.gmail.com', 587)

        s.starttls()

        try:
            s.login(sender_addr, password='debal247')

            text = msg.as_string()

            s.sendmail(sender_addr,reciever_addr,text)

        except:
            flag = -1

        finally:
            s.quit()

        return flag

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        flag = self.send_mail(tracker.get_slot('email'), tracker.get_slot('subject'), tracker.get_slot('content'))

        if flag == 1:
            dispatcher.utter_message(f"The mail sent successfully to {tracker.get_slot('email')}")

            return [SlotSet('email', None), SlotSet('subject', None), SlotSet('content', None)]

        else:
            dispatcher.utter_message(f'Please check the provided email again : {tracker.get_slot("email")}')
            return [SlotSet('email',None)]





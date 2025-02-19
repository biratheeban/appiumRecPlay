import json
import time
import logging
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

def get_activity_name(json_file):
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        
        if "events" in data and data["events"]:
            return data["events"][0]["activity"]
        else:
            return "No activity found in the JSON file."
    except Exception as e:
        return f"Error reading JSON file: {e}"

class WidgetInteractionReplayer:
    def __init__(self, device_name, app_package, host, json_file):
        self.options = UiAutomator2Options()
        self.options.platform_name = "Android"
        self.options.device_name = device_name
        self.options.app_package = app_package
        self.options.app_activity = get_activity_name(json_file)
        self.options.automation_name = "UiAutomator2"
        self.options.no_reset = True
        
        self.driver = webdriver.Remote(host, options=self.options)
        self.load_interactions(json_file)
    
    def load_interactions(self, json_file):
        with open(json_file, 'r') as f:
            self.interactions = json.load(f)['events']
    
    def replay_interactions(self):
        logging.info("Starting interaction replay...")
        for event in self.interactions:
            try:
                widget_id = event['widget']['id']
                action_type = event['type']
                
                element = self.driver.find_element(AppiumBy.ID, widget_id)
                
                if action_type == "click":
                    element.click()
                    logging.info(f"Replayed click on {widget_id}")
                elif action_type == "input":
                    element.send_keys("Test Input")
                    logging.info(f"Replayed input on {widget_id}")
                elif action_type == "swipe":
                    self.driver.swipe(
                        event['widget']['location']['x'],
                        event['widget']['location']['y'],
                        event['widget']['location']['x'] + 10,
                        event['widget']['location']['y'] + 10
                    )
                    logging.info(f"Replayed swipe on {widget_id}")
                
                time.sleep(0.5)
            except Exception as e:
                logging.error(f"Error replaying event: {e}")
    
    def cleanup(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    json_file = "widget_recording_20250219_103413.json"
    replayer = WidgetInteractionReplayer(
        device_name="emulator-5554",
        app_package="lk.bi007.testapp",
        host="http://192.168.1.187:4723",
        json_file=json_file
    )
    
    try:
        replayer.replay_interactions()
    finally:
        replayer.cleanup()

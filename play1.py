from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WidgetInteractionReplayer:
    def __init__(self, device_name, app_package, host):
        self.options = UiAutomator2Options()
        self.options.platform_name = "Android"
        self.options.device_name = device_name
        self.options.app_package = app_package
        self.options.automation_name = "UiAutomator2"
        self.options.no_reset = True
        
        self.host = host
        self.driver = None
        self._connect_to_appium()
    
    def _connect_to_appium(self):
        try:
            logging.info(f"Connecting to Appium server at {self.host}")
            self.driver = webdriver.Remote(self.host, options=self.options)
            logging.info("Successfully connected to Appium server")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Appium: {str(e)}")
    
    def load_and_replay(self, json_file, delay=0.5):
        try:
            # Load the JSON file
            with open(json_file, 'r') as f:
                recording = json.load(f)
            
            events = recording['events']
            logging.info(f"Loaded {len(events)} events from {json_file}")
            
            # Replay each event
            for i, event in enumerate(events, 1):
                try:
                    logging.info(f"Replaying event {i}/{len(events)}: {event['type']}")
                    self._replay_event(event)
                    time.sleep(delay)
                except Exception as e:
                    logging.error(f"Error replaying event {i}: {str(e)}")
        except Exception as e:
            logging.error(f"Error loading or replaying recording: {str(e)}")
    
    def _replay_event(self, event):
        try:
            widget = event['widget']
            element = self._find_element(widget)
            
            if element and element.is_displayed() and element.is_enabled():
                self._perform_action(element, event['type'])
        except Exception as e:
            logging.error(f"Error in replay_event: {str(e)}")
    
    def _find_element(self, widget):
        wait = WebDriverWait(self.driver, 5)
        try:
            # Try by ID first
            if widget.get('id'):
                try:
                    return wait.until(EC.presence_of_element_located((AppiumBy.ID, widget['id'])))
                except:
                    pass
            
            # Try by text
            if widget.get('text'):
                try:
                    return wait.until(EC.presence_of_element_located(
                        (AppiumBy.XPATH, f"//*[@text='{widget['text']}']")
                    ))
                except:
                    pass
            
            # Try by content description
            if widget.get('content_desc'):
                try:
                    return wait.until(EC.presence_of_element_located(
                        (AppiumBy.ACCESSIBILITY_ID, widget['content_desc'])
                    ))
                except:
                    pass
                    
        except Exception as e:
            logging.debug(f"Error finding element: {str(e)}")
        return None
    
    def _perform_action(self, element, action_type):
        try:
            if action_type == "click":
                element.click()
            elif action_type == "text_input":
                element.clear()
                element.send_keys("test input")
            elif action_type in ["checkbox", "selection"]:
                element.click()
            
            logging.info(f"Successfully performed {action_type}")
        except Exception as e:
            logging.error(f"Error performing {action_type}: {str(e)}")
    
    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    json_file = "interaction_log_20250220_125229.json"
    replayer = WidgetInteractionReplayer(
        device_name="emulator-5554",
        app_package="lk.bi007.testapp",
        host="http://192.168.1.187:4723",
    )
    
    try:
        replayer.load_and_replay(json_file)
    except KeyboardInterrupt:
        logging.info("\nReplaying interrupted by user")
    except Exception as e:
        logging.error(f"Error during replay: {str(e)}")
    finally:
        replayer.cleanup()
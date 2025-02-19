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

class WidgetInteractionRecorder:
    def __init__(self, device_name, app_package, host):
        self.options = UiAutomator2Options()
        self.options.platform_name = "Android"
        self.options.device_name = device_name
        self.options.app_package = app_package
        self.options.app_activity = f"{app_package}.MainActivity"
        self.options.automation_name = "UiAutomator2"
        self.options.no_reset = True
        
        self.driver = webdriver.Remote(host, options=self.options)
        self.actions = []
        self.last_recorded_events = set()
    
    def start_recording(self):
        try:
            while True:
                self._record_user_interactions()
                time.sleep(0.05)
        except KeyboardInterrupt:
            self.save_recording()
    
    def _record_user_interactions(self):
        try:
            touchable_widgets = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)'
            )
            
            for widget in touchable_widgets:
                try:
                    if widget.is_displayed() and widget.is_enabled():
                        widget_id = widget.get_attribute('resource-id')
                        action_type = self._get_widget_action(widget)
                        
                        if self._is_user_interaction(widget, widget_id):
                            widget_attrs = self._get_widget_attributes(widget)
                            event = {
                                'type': action_type,
                                'timestamp': datetime.now().isoformat(),
                                'activity': self.driver.current_activity,
                                'widget': widget_attrs
                            }
                            
                            event_signature = json.dumps(event, sort_keys=True)
                            if event_signature not in self.last_recorded_events:
                                self.record_event(event)
                                self.last_recorded_events.add(event_signature)
                
                except Exception as e:
                    logging.error(f"Error processing widget: {e}")
        except Exception as e:
            logging.error(f"Error recording widget interactions: {e}")
    
    def _is_user_interaction(self, widget, widget_id):
        """Ensures that the widget interaction is user-initiated."""
        try:
            WebDriverWait(self.driver, 0.3).until(
                EC.element_to_be_clickable((AppiumBy.ID, widget_id))
            )
            return True
        except:
            return False
    
    def _get_widget_action(self, widget):
        try:
            if "edittext" in widget.get_attribute("class").lower():
                return "input"
            elif widget.get_attribute("clickable") == "true":
                return "click"
            elif widget.get_attribute("scrollable") == "true":
                return "swipe"
            return "unknown"
        except:
            return "unknown"
    
    def _get_widget_attributes(self, widget):
        return {
            'id': widget.get_attribute('resource-id'),
            'text': widget.get_attribute('text'),
            'class': widget.get_attribute('class'),
            'location': widget.location,
            'size': widget.size,
            'bounds': widget.get_attribute('bounds'),
            'content_desc': widget.get_attribute('content-desc'),
            'package': widget.get_attribute('package')
        }
        
    def record_event(self, event):
        self.actions.append(event)
        logging.info(f"Recorded {event['type']} interaction with widget: {event['widget']['id']} ({event['widget']['text']})")
        
    def save_recording(self, filename=None):
        if filename is None:
            filename = f"widget_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        recording_data = {
            'app_package': self.options.app_package,
            'device_name': self.options.device_name,
            'recorded_at': datetime.now().isoformat(),
            'events': self.actions
        }
        
        with open(filename, 'w') as f:
            json.dump(recording_data, f, indent=2)
        logging.info(f"Recording saved to {filename}")
        
    def cleanup(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    recorder = WidgetInteractionRecorder(
        device_name="emulator-5554",
        app_package="lk.bi007.testapp",
        host="http://192.168.1.187:4723"
    )
    
    try:
        logging.info("Starting widget interaction recording... Press Ctrl+C to stop and save.")
        recorder.start_recording()
    except KeyboardInterrupt:
        logging.info("\nStopping recording...")
    finally:
        recorder.cleanup()

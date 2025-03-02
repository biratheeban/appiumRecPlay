from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import json
import time
import logging
import traceback

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WidgetInteractionRecorder:
    def __init__(self, device_name, app_package, host, connection_timeout=30):
        self.options = UiAutomator2Options()
        self.options.platform_name = "Android"
        self.options.device_name = device_name
        self.options.app_package = app_package
        self.options.automation_name = "UiAutomator2"
        self.options.no_reset = True
        
        # Add additional capabilities for better detection
        self.options.set_capability('androidDeviceReadyTimeout', 30)
        self.options.set_capability('autoGrantPermissions', True)
        self.options.set_capability('newCommandTimeout', 120)
        
        self.host = host
        self.connection_timeout = connection_timeout
        self.driver = None
        self.actions = []
        self.last_activity = None
        self.previous_elements_state = {}  # Track previous state of elements
        self.last_screen_state = None  # Store last screen state for comparison
        self.last_click_time = {}  # Track last click time for each element to prevent duplicates
        
        self._connect_to_appium()
        
    def _connect_to_appium(self):
        try:
            logging.info(f"Connecting to Appium server at {self.host}")
            self.driver = webdriver.Remote(self.host, options=self.options)
            logging.info("Successfully connected to Appium server")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Appium server: {str(e)}")

    def start_recording(self):
        try:
            logging.info("Starting interaction recording...")
            while True:
                try:
                    self._check_activity_change()
                    self._scan_for_interactions()
                    time.sleep(0.1)  # Faster scanning interval
                except WebDriverException as e:
                    logging.error(f"WebDriver error: {str(e)}")
                    break
                except Exception as e:
                    logging.error(f"Error during recording: {str(e)}")
                    traceback.print_exc()
                    time.sleep(1)
        except KeyboardInterrupt:
            logging.info("\nReceived stop signal. Stopping recording gracefully...")
        finally:
            self.save_recording()

    def _check_activity_change(self):
        try:
            current_activity = self.driver.current_activity
            if current_activity != self.last_activity:
                logging.info(f"Activity changed: {current_activity}")
                self.last_activity = current_activity
                self.previous_elements_state = {}  # Reset state tracking on activity change
                self.last_screen_state = None  # Reset screen state on activity change
                # Record activity change as an interaction
                self.actions.append({
                    'type': 'activity_change',
                    'timestamp': datetime.now().isoformat(),
                    'activity': current_activity,
                    'previous_activity': self.last_activity
                })
        except Exception as e:
            logging.debug(f"Error checking activity: {str(e)}")

    def _scan_for_interactions(self):
        """Enhanced interaction scanning with better detection"""
        try:
            # Capture current screen state for comparison
            current_screen_state = self._capture_screen_state()
            
            # Check if screen state has changed significantly
            screen_changed = self._has_screen_changed(current_screen_state)
            
            # Find different types of elements using multiple selectors
            
            # 1. Find all clickable elements
            clickable_elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.clickable(true)'
                '.enabled(true)'
            )
            
            # 2. Find all buttons specifically
            button_elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.className("android.widget.Button")'
                '.enabled(true)'
            )
            
            # Print details of all button elements for debugging
            print("\n----- BUTTON ELEMENTS FOUND -----")
            for i, btn in enumerate(button_elements):
                try:
                    btn_id = btn.get_attribute('resource-id')
                    btn_text = btn.get_attribute('text')
                    btn_content_desc = btn.get_attribute('content-desc')
                    btn_bounds = btn.get_attribute('bounds')
                    btn_class = btn.get_attribute('class')
                    print(f"Button {i+1}:")
                    print(f"  ID: {btn_id}")
                    print(f"  Text: {btn_text}")
                    print(f"  Content-Desc: {btn_content_desc}")
                    print(f"  Bounds: {btn_bounds}")
                    print(f"  Class: {btn_class}")
                    print(f"  Displayed: {btn.is_displayed()}")
                    print(f"  Enabled: {btn.get_attribute('enabled')}")
                    print(f"  Clickable: {btn.get_attribute('clickable')}")
                    print("---")
                except Exception as e:
                    print(f"Error getting button {i+1} details: {str(e)}")
            print("--------------------------------\n")
            
            # 3. Find elements with text
            text_elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.textMatches(".*")'
                '.enabled(true)'
            )
            
            # 4. Find input elements specifically
            input_elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.className("android.widget.EditText")'
            )
            
            # 5. Find elements with content description
            content_desc_elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.descriptionMatches(".*")'
                '.enabled(true)'
            )
            
            # 6. Find ImageButton elements
            image_button_elements = self.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector()'
                '.className("android.widget.ImageButton")'
                '.enabled(true)'
            )
            
            # Print image button elements too
            print("\n----- IMAGE BUTTON ELEMENTS FOUND -----")
            for i, btn in enumerate(image_button_elements):
                try:
                    btn_id = btn.get_attribute('resource-id')
                    btn_content_desc = btn.get_attribute('content-desc')
                    btn_bounds = btn.get_attribute('bounds')
                    print(f"ImageButton {i+1}:")
                    print(f"  ID: {btn_id}")
                    print(f"  Content-Desc: {btn_content_desc}")
                    print(f"  Bounds: {btn_bounds}")
                    print(f"  Displayed: {btn.is_displayed()}")
                    print("---")
                except Exception as e:
                    print(f"Error getting image button {i+1} details: {str(e)}")
            print("--------------------------------\n")
            
            # Combine all elements
            elements = clickable_elements + button_elements + text_elements + input_elements + content_desc_elements + image_button_elements
            
            # Remove duplicates by converting to dictionary with element ID as key
            element_dict = {}
            for element in elements:
                try:
                    element_id = self._get_element_identifier(element)
                    if element_id and element.is_displayed():
                        element_dict[element_id] = element
                except:
                    pass
            
            # Get unique elements
            unique_elements = list(element_dict.values())
            
            logging.debug(f"Found {len(unique_elements)} potential interactive elements")
            
            current_elements_state = {}
            for element in unique_elements:
                try:
                    element_id = self._get_element_identifier(element)
                    if not element_id:
                        continue
                        
                    # Get current state
                    current_state = self._get_element_state(element)
                    current_elements_state[element_id] = current_state
                    
                    # Three ways to detect interactions:
                    # 1. State has changed for the element
                    state_changed = self._has_state_changed(element_id, current_state)
                    
                    # 2. Element is newly focused (for text inputs)
                    is_newly_focused = (
                        current_state.get('focused') == 'true' and
                        (element_id not in self.previous_elements_state or
                         self.previous_elements_state[element_id].get('focused') != 'true')
                    )
                    
                    # 3. Button click detection (if screen changed and element is a button or clickable)
                    is_button_click = (
                        screen_changed and 
                        (("button" in element.get_attribute('class').lower()) or
                         (element.get_attribute('clickable') == 'true' and element.get_attribute('text'))) and
                        self._is_likely_clicked(element_id)
                    )
                    
                    if state_changed or is_newly_focused or is_button_click:
                        action_type = self._determine_action_type(element, current_state, 
                                                               is_newly_focused, is_button_click)
                        self._record_interaction(element, current_state, action_type)
                    
                except Exception as e:
                    logging.debug(f"Error processing element: {str(e)}")
            
            # Update previous states
            self.previous_elements_state = current_elements_state
            self.last_screen_state = current_screen_state
            
        except Exception as e:
            logging.error(f"Error in scanning interactions: {str(e)}")
            traceback.print_exc()

    def _capture_screen_state(self):
        """Capture a simplified representation of the current screen state"""
        try:
            # Get page source as a screen state representation
            page_source = self.driver.page_source
            
            # We could compute a hash, but for simplicity, let's just use a shortened version
            return page_source[:1000] if page_source else None
        except Exception as e:
            logging.debug(f"Error capturing screen state: {str(e)}")
            return None

    def _has_screen_changed(self, current_state):
        """Check if the screen has changed significantly"""
        if not self.last_screen_state or not current_state:
            return False
        
        # Simple comparison - in a more sophisticated version, you could use diff algorithms
        return self.last_screen_state != current_state

    def _is_likely_clicked(self, element_id):
        """Determine if an element was likely clicked based on timing"""
        current_time = time.time()
        
        # If we've never seen this element before, it's not a repeat click
        if element_id not in self.last_click_time:
            self.last_click_time[element_id] = current_time
            return True
            
        # Check if enough time has passed since last click (to avoid duplicates)
        time_diff = current_time - self.last_click_time[element_id]
        if time_diff > 0.5:  # 500ms threshold
            self.last_click_time[element_id] = current_time
            return True
            
        return False

    def _get_element_identifier(self, element):
        """Get a unique identifier for the element"""
        try:
            resource_id = element.get_attribute('resource-id')
            if resource_id:
                return resource_id
            
            # Fallback to creating a composite ID
            bounds = element.get_attribute('bounds')
            text = element.get_attribute('text')
            class_name = element.get_attribute('class')
            content_desc = element.get_attribute('content-desc')
            
            return f"{class_name}_{bounds}_{text}_{content_desc}"
        except:
            return None

    def _get_element_state(self, element):
        """Get comprehensive element state"""
        try:
            return {
                'selected': element.get_attribute('selected'),
                'checked': element.get_attribute('checked'),
                'focused': element.get_attribute('focused'),
                'text': element.get_attribute('text'),
                'content-desc': element.get_attribute('content-desc'),
                'enabled': element.get_attribute('enabled'),
                'clickable': element.get_attribute('clickable'),
                'bounds': element.get_attribute('bounds'),
                'displayed': element.is_displayed()
            }
        except Exception as e:
            logging.debug(f"Error getting element state: {str(e)}")
            return {}

    def _has_state_changed(self, element_id, current_state):
        """Check if element state has changed meaningfully"""
        if element_id not in self.previous_elements_state:
            return False
            
        prev_state = self.previous_elements_state[element_id]
        
        # Check for meaningful state changes - expanded to detect more changes
        important_attrs = ['selected', 'checked', 'focused', 'text', 'enabled']
        return any(
            current_state.get(attr) != prev_state.get(attr)
            for attr in important_attrs
            if attr in current_state and attr in prev_state
        )

    def _determine_action_type(self, element, state, is_newly_focused=False, is_button_click=False):
        """Enhanced action type detection"""
        try:
            class_name = element.get_attribute("class").lower()
            
            # Direct detection based on flags
            if is_button_click:
                return "button_click"
                
            if is_newly_focused and "edittext" in class_name:
                return "text_input"
                
            # Standard detection logic
            if "edittext" in class_name:
                return "text_input" if state.get('focused') == "true" else "unknown"
            elif "button" in class_name and state.get('clickable') == "true":
                return "button_click"
            elif "imagebutton" in class_name:
                return "button_click"
            elif state.get('checked') == "true":
                return "checkbox"
            elif state.get('selected') == "true":
                return "selection"
            elif element.get_attribute("clickable") == "true":
                return "click"
            elif element.get_attribute("scrollable") == "true":
                return "scroll"
                
            return "unknown"
        except:
            return "unknown"

    def _record_interaction(self, element, state, action_type="unknown"):
        """Record detected interaction with enhanced logging"""
        try:
            if action_type == "unknown":
                action_type = self._determine_action_type(element, state)
                
            if action_type != "unknown":
                widget_attrs = self._get_widget_attributes(element)
                
                event = {
                    'type': action_type,
                    'timestamp': datetime.now().isoformat(),
                    'activity': self.last_activity,
                    'widget': widget_attrs,
                    'state_change': state
                }
                
                self.actions.append(event)
                logging.info(
                    f"[{event['activity']}] {action_type.upper()}: "
                    f"{widget_attrs.get('id', 'no-id')} - {widget_attrs.get('text', 'N/A')}"
                )
                
                # Debug logging
                logging.debug(f"Recorded interaction details: {json.dumps(event, indent=2)}")
                
        except Exception as e:
            logging.error(f"Error recording interaction: {str(e)}")
            traceback.print_exc()

    def _get_widget_attributes(self, element):
        """Get comprehensive widget attributes"""
        try:
            return {
                'id': element.get_attribute('resource-id'),
                'text': element.get_attribute('text'),
                'class': element.get_attribute('class'),
                'content_desc': element.get_attribute('content-desc'),
                'package': element.get_attribute('package'),
                'activity': self.last_activity,
                'bounds': element.get_attribute('bounds'),
                'clickable': element.get_attribute('clickable'),
                'enabled': element.get_attribute('enabled'),
                'focusable': element.get_attribute('focusable')
            }
        except Exception as e:
            logging.debug(f"Error getting widget attributes: {str(e)}")
            return {'error': str(e)}

    def save_recording(self, filename=None):
        if not self.actions:
            logging.info("No interactions recorded. Skipping save.")
            return
            
        if filename is None:
            filename = f"interaction_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        recording_data = {
            'app_package': self.options.app_package,
            'device_name': self.options.device_name,
            'recorded_at': datetime.now().isoformat(),
            'total_activities': len(set(event['activity'] for event in self.actions if 'activity' in event)),
            'total_interactions': len(self.actions),
            'events': self.actions
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(recording_data, f, indent=2)
            logging.info(f"Recording saved to {filename} ({len(self.actions)} events)")
        except Exception as e:
            logging.error(f"Error saving recording: {str(e)}")

    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

if __name__ == "__main__":
    recorder = WidgetInteractionRecorder(
        device_name="emulator-5554",
        app_package="lk.bi007.testapp",
        host="http://localhost:4723"
    )
    
    try:
        recorder.start_recording()
    except KeyboardInterrupt:
        logging.info("\nStopping recording...")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        traceback.print_exc()
    finally:
        recorder.cleanup()
import math
import logging
import obspython as obs

from datetime import datetime
from pathlib import Path


SEP = ";"
SCRIPT_DIR_PATH = Path(__file__).parent
DEFAULT_RECORD_FILE_DIRECTORY_PATH = SCRIPT_DIR_PATH
RECORD_FIGHT_TIME_HOTKEY_ID = obs.OBS_INVALID_HOTKEY_ID
DEFAULT_RECORD_FILE_NAME = "fight_records.txt"
RECORD_FILE_PATH = SCRIPT_DIR_PATH / DEFAULT_RECORD_FILE_NAME
CLEAR_RECORD_STARTED = False
GLOBAL_SETTINGS = None
DEBUG_MODE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def script_description():
    return """
    <center>
    <h2>Albion Stream Helper Script</h2>    
    </center>
    <h4 align="right">
    by Frederico Damian'th'. <a href="https://github.com/fredericodamian/albion_stream_helper_script"> Source</a>
    </h4>
    <h5 align="left"> Instructions: </h5>
    <ol>
    <li>Select a directory to store the record file.</li>
    <li>Configure hotkey for 'Register Fight Time' at HotKeys configuration.</li>
    <li>Fight!</li>
    </ol>
    <hr/>
    </p>
    """


def script_properties():
    props = obs.obs_properties_create()

    record_dir_prop = obs.obs_properties_add_path(
        props,
        "record_file_directory_path",
        "Record File Directory",
        obs.OBS_PATH_DIRECTORY,
        None,
        DEFAULT_RECORD_FILE_DIRECTORY_PATH.as_posix(),
    )
    obs.obs_property_set_modified_callback(record_dir_prop, on_record_file_directory_path_modified)
    obs.obs_properties_add_button(props, "manual_record_button", "Record now", on_record_fight_time_hotkey_clicked)
    obs.obs_properties_add_button(props, "clear_records_button", "Clear Records", clear_records_button_clicked)
    obs.obs_properties_add_button(
        props,
        "confirm_clear_records_button",
        "Confirm",
        confirm_clear_records_button_clicked,
    )
    obs.obs_properties_add_button(
        props,
        "cancel_clear_records_button",
        "Cancel",
        cancel_clear_records_button_clicked,
    )

    set_visibility_clear_records_confirmation(props, CLEAR_RECORD_STARTED)

    obs.obs_properties_apply_settings(props, GLOBAL_SETTINGS)
    return props


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "record_file_directory_path", SCRIPT_DIR_PATH.as_posix())
    update_record_file_variable(settings)


def script_update(settings):
    global GLOBAL_SETTINGS
    GLOBAL_SETTINGS = settings
    update_record_file_variable(settings)


def script_load(settings):
    RECORD_FIGHT_TIME_HOTKEY_ID = obs.obs_hotkey_register_frontend(
        SCRIPT_DIR_PATH.as_posix(), "Record Fight Time", on_record_fight_time_hotkey_clicked
    )
    global CLEAR_RECORD_STARTED
    CLEAR_RECORD_STARTED = False
    hotkey_save_array = obs.obs_data_get_array(settings, "record_fight_time_hotkey")
    obs.obs_hotkey_load(RECORD_FIGHT_TIME_HOTKEY_ID, hotkey_save_array)
    obs.obs_data_array_release(hotkey_save_array)
    update_record_file_variable(settings)


def script_unload():
    global CLEAR_RECORD_STARTED
    CLEAR_RECORD_STARTED = False


def script_save(settings):
    hotkey_reset_save_array = obs.obs_hotkey_save(RECORD_FIGHT_TIME_HOTKEY_ID)
    obs.obs_data_set_array(settings, "record_fight_time_hotkey", hotkey_reset_save_array)
    obs.obs_data_array_release(hotkey_reset_save_array)


def on_record_fight_time_hotkey_clicked(props, prop):
    streaming_output = obs.obs_frontend_get_streaming_output()

    # Check if its streaming
    if not is_streaming(streaming_output):
        logger.info("Can't get streaming duration because you're not streaming!")
        return None

    register_fight_in_record_file()


def on_record_file_directory_path_modified(props, prop, settings):
    update_record_file_variable(settings)


def update_record_file_variable(settings):
    record_file_directory_path = obs.obs_data_get_string(settings, "record_file_directory_path")
    if record_file_directory_path == "":
        record_file_directory_path = SCRIPT_DIR_PATH.as_posix()

    global RECORD_FILE_PATH
    global DEFAULT_RECORD_FILE_NAME
    RECORD_FILE_PATH = Path(record_file_directory_path) / DEFAULT_RECORD_FILE_NAME


def create_fight_record_file():
    if RECORD_FILE_PATH.exists():
        return

    headers = ["STREAMING TIME", "DAY DATE TIME"]
    header_string = SEP.join(headers)
    with open(RECORD_FILE_PATH.as_posix(), "w+") as file:
        file.write(f"{header_string}\n")


def register_fight_in_record_file():
    if not RECORD_FILE_PATH.exists():
        create_fight_record_file()

    streaming_time = get_current_time_streaming()
    date_string_text = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    data_line_list = [streaming_time, date_string_text]
    data_line_string = SEP.join(data_line_list)

    with open(RECORD_FILE_PATH.as_posix(), "a") as file:
        file.write(f"{data_line_string}\n")


def is_streaming(streaming_output):
    global DEBUG_MODE
    return DEBUG_MODE is True or streaming_output is not None


def get_current_time_streaming():
    streaming_output = obs.obs_frontend_get_streaming_output()
    # Check if its streaming
    if not is_streaming(streaming_output):
        logger.info("Can't get streaming duration because you're not streaming!")
        return "STREAMING OFF"

    fps = obs.obs_get_active_fps()
    total_frames = obs.obs_output_get_total_frames(streaming_output)
    streaming_duration_total_seconds = total_frames / fps

    # Free memory
    obs.obs_output_release(streaming_output)

    # Apply string format
    streaming_hours = "{}".format(math.floor(streaming_duration_total_seconds / 3600))
    streaming_minutes = "{}".format(math.floor((streaming_duration_total_seconds % 3600) / 60))
    streaming_seconds = "{}".format(math.floor(0.5 + streaming_duration_total_seconds % 60))

    if len(streaming_hours) <= 1:
        streaming_hours = "0" + streaming_hours

    if len(streaming_minutes) <= 1:
        streaming_minutes = "0" + streaming_minutes

    if len(streaming_seconds) <= 1:
        streaming_seconds = "0" + streaming_seconds

    streaming_duration_string = "{}:{}:{}".format(streaming_hours, streaming_minutes, streaming_seconds)

    return streaming_duration_string


def clear_records_button_clicked(props, prop):
    global CLEAR_RECORD_STARTED
    if not RECORD_FILE_PATH.exists() or CLEAR_RECORD_STARTED:
        return False

    CLEAR_RECORD_STARTED = True
    set_visibility_clear_records_confirmation(props, True)
    return True


def confirm_clear_records_button_clicked(props, prop):
    global CLEAR_RECORD_STARTED
    if not CLEAR_RECORD_STARTED:
        return False

    RECORD_FILE_PATH.unlink()
    create_fight_record_file()
    CLEAR_RECORD_STARTED = False
    set_visibility_clear_records_confirmation(props, False)
    return True


def cancel_clear_records_button_clicked(props, prop):
    global CLEAR_RECORD_STARTED
    if not CLEAR_RECORD_STARTED:
        return False

    CLEAR_RECORD_STARTED = False
    set_visibility_clear_records_confirmation(props, False)
    return True


def set_visibility_clear_records_confirmation(props, mode):
    obs.obs_property_set_enabled(obs.obs_properties_get(props, "clear_records_button"), not mode)
    obs.obs_property_set_visible(obs.obs_properties_get(props, "confirm_clear_records_button"), mode)
    obs.obs_property_set_visible(obs.obs_properties_get(props, "cancel_clear_records_button"), mode)

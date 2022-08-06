-- Version 0.0.1
obs = obslua

SEP = ";"
DEFAULT_RECORD_FILE_DIRECTORY_PATH = DEFAULTBASE
RECORD_FIGHT_TIME_HOTKEY_ID = obs.OBS_INVALID_HOTKEY_ID
RECORD_FILE_PATH = nil
function script_description()
    return [[
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
    ]]
end

function script_properties()
    local props = obs.obs_properties_create()

    record_dir_prop = obs.obs_properties_add_path(props, "record_file_directory_path", "Record File Directory",
        obs.OBS_PATH_DIRECTORY ,
        nil,
        DEFAULT_RECORD_FILE_DIRECTORY_PATH
    )
    obs.obs_property_set_modified_callback(record_dir_prop, on_record_file_directory_path_modified)
    obs.obs_properties_add_button(props, "manual_record_button", "Record now", on_record_fight_time_hotkey_clicked)
    obs.obs_properties_add_button(props, "reset_records_button", "Reset Records", reset_records_button_clicked)
    return props
end

function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "record_file_directory_path", script_path())
    update_record_file_variable(settings)
end

function script_update(settings)
    update_record_file_variable(settings)
end

function script_load(settings)
  RECORD_FIGHT_TIME_HOTKEY_ID = obs.obs_hotkey_register_frontend(script_path(), "Record Fight Time", on_record_fight_time_hotkey_clicked)
  local hotkey_save_array = obs.obs_data_get_array(settings, "record_fight_time_hotkey")
  obs.obs_hotkey_load(RECORD_FIGHT_TIME_HOTKEY_ID, hotkey_save_array)
  obs.obs_data_array_release(hotkey_save_array)
  update_record_file_variable(settings)
end

function script_unload()

end

function script_save(settings)
    local hotkey_reset_save_array = obs.obs_hotkey_save(RECORD_FIGHT_TIME_HOTKEY_ID)
    obs.obs_data_set_array(settings, "record_fight_time_hotkey", hotkey_reset_array)
    obs.obs_data_array_release(hotkey_reset_array)
end


function on_record_fight_time_hotkey_clicked(pressed)
    local streaming_output = obs.obs_frontend_get_streaming_output();

    -- Check if its streaming
	if streaming_output == nil then
        error("Can't get streaming duration because you're not streaming!")
        return nil
    end
    
    register_fight_in_record_file()
end

function on_record_file_directory_path_modified(props, prop, settings)
    update_record_file_variable(settings)
end

function update_record_file_variable(settings)
    local record_file_directory_path = obs.obs_data_get_string(settings, "record_file_directory_path")
    if record_file_directory_path == "" then
        record_file_directory_path = script_path()
    end

    RECORD_FILE_PATH = record_file_directory_path .. "/" .. "fight_records.txt"
end

function file_exists(file)
    local f = io.open(file, "rb")
    if f then f:close() end
    return f ~= nil
end

function create_fight_record_file()
    if file_exists(RECORD_FILE_PATH) then
        return
    end

    header = "STREAMING TIME" .. SEP .. "DAY DATE TIME"
    file = io.open(RECORD_FILE_PATH, "w+")
    file:write(header, "\n")
    file:close()
end

function register_fight_in_record_file()
    if not file_exists(RECORD_FILE_PATH) then
        create_fight_record_file()
    end

    local streaming_time = get_current_time_streaming()
    local date_string_text = os.date("%Y/%m/%d %H:%M:%S")
    local text = streaming_time .. SEP .. date_string_text

    file = io.open(RECORD_FILE_PATH, "a")
    file:write(text, "\n")
    file:close()
end

function get_current_time_streaming()
    local streaming_output = obs.obs_frontend_get_streaming_output();

	-- Check if its streaming
	if streaming_output == nil then
        error("Can't get streaming duration because you're not streaming!")
        return "STREAMING OFF"
    end

    local fps = obs.obs_get_active_fps();
    local total_frames = obs.obs_output_get_total_frames(streaming_output);
    streaming_duration_total_seconds =  total_frames / fps;

    -- Free memory
    obs.obs_output_release(streaming_output);

    -- Apply string format
    local streaming_hours = string.format("%d", math.floor(streaming_duration_total_seconds / 3600));
    local streaming_minutes = string.format("%d", math.floor((streaming_duration_total_seconds % 3600) / 60));
    local streaming_seconds = string.format("%d", math.floor(0.5 + streaming_duration_total_seconds % 60));

    if string.len(streaming_hours) <= 1 then
        streaming_hours = "0" .. streaming_hours;
    end

    if string.len(streaming_minutes) <= 1 then
        streaming_minutes = "0" .. streaming_minutes;
    end

    if string.len(streaming_seconds) <= 1 then
        streaming_seconds = "0" .. streaming_seconds;
    end

    streaming_duration_string = string.format("%s:%s:%s", streaming_hours, streaming_minutes, streaming_seconds);

    return streaming_duration_string
end

function reset_records_button_clicked(pressed)
    if not file_exists(RECORD_FILE_PATH) then
        return
    end

    os.remove(RECORD_FILE_PATH)
    create_fight_record_file()
end
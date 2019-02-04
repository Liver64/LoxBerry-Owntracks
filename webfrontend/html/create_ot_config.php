<?php

##############################################################################################################################
#
# Version: 	0.0.1
# Datum: 	31.01.2019
# veröffentlicht in: https://github.com/Liver64/LoxBerry-Owntracks/releases
# 
##############################################################################################################################

// ToDo

// filter only owntracks topics for HTML output_add_rewrite_var
// pass Name from UI to PHP to create config file
// add time to config file name
// re-number users after deletion

header('Content-Type: text/html; charset=utf-8');

require_once "loxberry_system.php";
require_once "loxberry_log.php";
include "system/error.php";

error_reporting(E_ALL);
ini_set("display_errors", "off");
define('ERROR_LOG_FILE', "$lbplogdir/owntracks.log");

# calling custom error handler
set_error_handler("handleError");

# Testcase for error handler
//print_r($arra); 							// undefined variable

ini_set('max_execution_time', 60); 			// Max. Skriptlaufzeit auf 60 Sekunden
date_default_timezone_set(date("e"));		// setze korrekte Zeitzone
register_shutdown_function('shutdown');

# Includes
require_once("system/Helper.php");
require_once("system/logging.php");

# declare variables/constants

$home = $lbhomedir;
$hostname = gethostname();										// hostname LoxBerry
$myIP = $_SERVER["SERVER_ADDR"];								// get IP of LoxBerry
$syntax = $_SERVER['REQUEST_URI'];								// get syntax
$psubfolder = $lbpplugindir;									// get pluginfolder
$lbversion = LBSystem::lbversion();								// get LoxBerry Version
$path = LBSCONFIGDIR; 											// get path to general.cfg
$myFolder = "$lbpconfigdir";									// get config folder
$logpath = "$lbplogdir/$psubfolder";							// get log folder
$templatepath = "$lbptemplatedir";								// get templatedir
$lbport = lbwebserverport();									// get loxberry port
$ot_template_file = $myFolder."/config_template.otrc";
$topic = "owntracks/#";											// topic for MQTT
$topic_conv_enter = "enter=1";									// conversion for enter
$topic_conv_leave = "leave=0";									// conversion for leave
$last_mqtt_json_data = "/run/shm/mqttgateway_topics.json";		// path to MQTT JSON data
$mqtt_config = "$lbhomedir/config/plugins/mqttgateway/mqtt.json";			// path to MQTT configuration
$mqtt_cred = "$lbhomedir/config/plugins/mqttgateway/cred.json";				// path to MQTT login credentials
$datafile = "/dev/shm/mqttgateway_topics.json";

echo '<PRE>';

$params = [	"name" => "Owntracks PHP",
			"filename" => "$lbplogdir/owntracks.log",
			"append" => 1,
			"addtime" => 1,
			];
$log = LBLog::newLog($params);
$level = LBSystem::pluginloglevel();
$plugindata = LBSystem::plugindata();
$L = LBSystem::readlanguage("owntracks.ini");

LOGSTART("PHP started");

# get data from POST
$uname = ($_POST);


$ot_topics = topics($datafile);
$cred = get_mqtt_cred($mqtt_cred);
$config = get_mqtt_config($mqtt_config);
update_mqtt_config($topic, $topic_conv_enter, $topic_conv_leave);
$ot_config_file = read_tmpl_config_file($ot_template_file);
$tmp_ot = plugin_config();
$FileNameOT = prepare_config_file($ot_config_file, $tmp_ot, $cred);

# return file name to Plugin
echo($FileNameOT);

# get credentials
function get_mqtt_cred($FileName)  {
	$cred = File_Get_Array_From_JSON($FileName, $zip=false);
	//print_r($cred);
	return $cred;
}

# get config
function get_mqtt_config($FileName)  {
	$config = File_Get_Array_From_JSON($FileName, $zip=false);
	define("CONFIG", $config);
	//print_r($config);
	return $config;
}

# check if topic and conversion(s) exist, if not update mqtt.json
function update_mqtt_config($topic, $topic_conv_enter, $topic_conv_leave)   {
	global $config, $mqtt_config;
	
	$save_conf = "";
	LOGGING("Check for missing data in MQTT Plugin will be executed",7);
	$key_topic = array_search($topic, $config['subscriptions']);
	if ($key_topic === false)  {
		array_push($config['subscriptions'],$topic);
		$save_conf = "1";
		LOGGING("Owntracks topic 'owntracks/#' has been added to mqtt.json",7);
	}
	$key_enter = array_search($topic_conv_enter, $config['conversions']);
	if ($key_enter === false)  {
		array_push($config['conversions'],$topic_conv_enter);
		$save_conf = "1";
		LOGGING("Owntracks conversion 'enter=1' has been added to mqtt.json",7);
	}
	$key_leave = array_search($topic_conv_leave, $config['conversions']);
	if ($key_leave === false)  {
		array_push($config['conversions'],$topic_conv_leave);
		$save_conf = "1";
		LOGGING("Owntracks conversion 'leave=0' has been added to mqtt.json",7);
	}
	if ($save_conf == "1")  {
		//print_r($config);
		File_Put_Array_As_JSON($mqtt_config, $config, $zip=false);
		LOGGING("file 'mqtt.json' has been successful updated",7);
	} else {
		LOGGING("Nothing to do, data already there",7);
	}
}

# read config template file
function read_tmpl_config_file($FileName)  {
	
	$ot_config_file = File_Get_Array_From_JSON($FileName, $zip=false);
	//print_r($ot_config_file);
	return $ot_config_file;
}

# read plugin config 
function plugin_config()  {
	global $myFolder;
	
	if (!file_exists($myFolder.'/owntracks.cfg')) {
		LOGGING('The file owntracks.cfg could not be opened, please try again!', 4);
	} else {
		$tmp_ot = parse_ini_file($myFolder.'/owntracks.cfg', TRUE);
		if ($tmp_ot === false)  {
			LOGGING("The file 'owntracks.cfg' could not be parsed, the file may be disruppted. Please check/save your Plugin Config or check file 'owntracks.cfg' manually!", 3);
			exit(1);
		}
		LOGGING("Owntracks config has been loaded",7);
	}
	//print_r($tmp_ot);
	return $tmp_ot;
}

# prepare and save OT config file
function prepare_config_file($ot_config_file, $tmp_ot, $cred)  {
	
	global $uname, $L;
	
	//print_r($cred);
	//print_r($tmp_ot);
	//print_r($ot_config_file);
	$ot_config_file['host'] = $tmp_ot['CONNECTION']['dyndns'];
	$ot_config_file['port'] = $tmp_ot['CONNECTION']['port'];
	$ot_config_file['username'] = $cred['Credentials']['brokeruser'];
	$ot_config_file['password'] = $cred['Credentials']['brokerpass'];
	$ot_config_file['deviceId'] = $tmp_ot['USER']['name'][3];
	$ot_config_file['waypoints'][0]['lat'] = $tmp_ot['LOCATION']['latitude'];
	$ot_config_file['waypoints'][0]['lon'] = $tmp_ot['LOCATION']['longitude'];
	$ot_config_file['waypoints'][0]['rad'] = $tmp_ot['LOCATION']['radius'];
	$ot_config_file['waypoints'][0]['desc'] = $tmp_ot['LOCATION']['location'];
	$ot_config_file['waypoints'][0]['tst'] = time();
	LOGGING("Owntracks App configfile has been created", 7);
	// print_r($ot_config_file);
	$FileNameOT = LBPDATADIR."/OT_".$uname['username']."_".$tmp_ot['LOCATION']['location']."_".$tmp_ot['LOCATION']['radius']."_".date("Ymd").".otrc";
	$Fname = $L['VALIDATION.SAVE_FILE']. " '".$uname['username']."_".$tmp_ot['LOCATION']['location']."_".$tmp_ot['LOCATION']['radius']."_".date("Ymd").".otrc' ".$L['VALIDATION.SAVE_FILE_WHERE'];
	//echo $FileNameOT;
	File_Put_Array_As_JSON($FileNameOT, $ot_config_file, $zip=false);
	LOGGING("Owntracks App configfile has been saved to data folder", 5);
	//return $ot_config_file;
	return($Fname);
}

# get topics
function topics($FileName)  {
	$ot_topics = File_Get_Array_From_JSON($FileName, $zip=false);
	//print_r($ot_topics);
	return $ot_topics;
}

function shutdown()
{
	global $log;
	$log->LOGEND("PHP finished");
}
?>
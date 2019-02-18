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

#echo '<PRE>';

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
$postData = ($_POST);

#$postData = array();
// error handling if no data been recived
if (empty($postData)) {
	header('HTTP/1.1 500 '.$L['ERRORS.ERR_POST_PHP']);
    header('Content-Type: application/json; charset=UTF-8');
    die(json_encode(array('message' => 'ERROR', 'code' => 1337)));
	exit(1);
}

$ot_topics = topics($datafile);
$credentials = get_mqtt_cred($mqtt_cred);
$config = get_mqtt_config($mqtt_config);
$valid_config = validate_mqtt_config($config);
update_mqtt_config($topic, $topic_conv_enter, $topic_conv_leave);
$ot_config_file = read_tmpl_config_file($ot_template_file);
$FileNameOT = prepare_config_file($ot_config_file, $credentials);


##########################################################################################
### return file name to Plugin
echo($FileNameOT);
##########################################################################################

#$delimiter = chr(1);
#$eoldelimiter = chr(2) . "\n";
#$fp = fopen('/etc/default/ot-recorder','r');
#while (!feof($fp)) {
#    $line = stream_get_line($fp, 4096, $eoldelimiter); //use 2048 if very long lines

#    if ($line[0] === '#' or $line[0] === '//') continue;  //Skip lines that start with #
#    $loop++;
#	my_filter($line);
#}

#function my_filter($var){
#    return $var[0] != '#';
# }
 #$array = array_filter(file('/etc/default/ot-recorder'),'my_filter');

#print_r($array);
#exit;
#"/etc/default/ot-recorder"

# get credentials
function get_mqtt_cred($FileName)  {
	$credentials = File_Get_Array_From_JSON($FileName, $zip=false);
	//print_r($credentials);
	return $credentials;
}

# get config
function get_mqtt_config($FileName)  {
	$config = File_Get_Array_From_JSON($FileName, $zip=false);
	define("CONFIG", $config);
	//print_r($config);
	return $config;
}

# validate MQTT config
function validate_mqtt_config($config)  {
	LOGGING("Execute check off MQTT Plugin settings...",7);
	if (($config['Main']['use_http'] === false) and ($config['Main']['use_udp'] === false))  {
		LOGGING("Sending data to Miniserver is turned off in MQTT Plugin (neither HTTP nore UDP). Please turn on!!",3);
	}
	if ($config['Main']['expand_json'] === false)  {
		LOGGING("The option 'Expand JSON data' is turned off in MQTT Plugin. Please turn on otherwise data conversion does not take place and you can't get 'enter/leave' events into MS!!",4);
		LOGGING("Please check also if there are any conflicts with other MQTT data you already pass to Miniserver!",4);
	}
	if ($config['Main']['convert_booleans'] === false)  {
		LOGGING("The option 'Convert booleans to 1 and 0' is turned off in MQTT Plugin. Please turn on if you don't receive data in MS in the correct format!",6);
	}
	LOGGING("Execute check off MQTT Plugin completed",5);
}

# check if topic and conversion(s) exist, if not update mqtt.json
function update_mqtt_config($topic, $topic_conv_enter, $topic_conv_leave)   {
	global $config, $mqtt_config, $topic_conv_enter, $topic_conv_leave;
	
	$save_conf = "";
	LOGGING("Check for missing data in MQTT Plugin will be executed",7);
	$key_topic = array_search($topic, $config['subscriptions']);
	if ($key_topic === false)  {
		array_push($config['subscriptions'],$topic);
		$save_conf = "1";
		LOGGING("Owntracks topic 'owntracks/#' has been added to mqtt.json",7);
	}
	if ($config['conversions'] != NULL)  {
		$key_enter = array_search($topic_conv_enter, $config['conversions']);
		if ($key_enter === false)  {
			echo "key enter: ".$topic_conv_enter."<br>";
			array_push($config['conversions'],$topic_conv_enter);
			$save_conf = "1";
			LOGGING("Owntracks conversion 'enter=1' has been added to mqtt.json",7);
		}
	} else {
		echo "topic: ".$topic_conv_enter."<br>";
		array_push($config['conversions'],$topic_conv_enter);
		print_r($config);
		$save_conf = "1";
		LOGGING("Owntracks conversion 'enter=1' has been added to mqtt.json",7);
	}
	if (array_key_exists("conversions", $config))  {
		$key_leave = array_search($topic_conv_leave, $config['conversions']);
		if ($key_leave === false)  {
			array_push($config['conversions'],$topic_conv_leave);
			$save_conf = "1";
			LOGGING("Owntracks conversion 'leave=0' has been added to mqtt.json",7);
		}
	} else {
		array_push($config['conversions'],$topic_conv_leave);
		$save_conf = "1";
		LOGGING("Owntracks conversion 'leave=0' has been added to mqtt.json",7);
	}
	if ($save_conf == "1")  {
		print_r($config);
		File_Put_Array_As_JSON($mqtt_config, $config, $zip=false);
		LOGGING("file 'mqtt.json' has been successful updated",7);
	} else {
		LOGGING("Nothing to do, data already there",7);
	}
	//print_r($config);
}

# read config template file
function read_tmpl_config_file($FileName)  {
	
	$ot_config_file = File_Get_Array_From_JSON($FileName, $zip=false);
	//print_r($ot_config_file);
	return $ot_config_file;
}

# prepare and save OT config file
function prepare_config_file($ot_config_file, $credentials)  {
	
	global $uname, $L, $postData;
	
	//print_r($credentials);
	//print_r($tmp_ot);
	//print_r($ot_config_file);
	$ot_config_file['host'] = $postData['dyndns'];
	$ot_config_file['port'] = $postData['port'];
	$ot_config_file['username'] = $credentials['Credentials']['brokeruser'];
	$ot_config_file['password'] = $credentials['Credentials']['brokerpass'];
	$ot_config_file['deviceId'] = $postData['name'];
	$ot_config_file['waypoints'][0]['lat'] = $postData['latitude'];
	$ot_config_file['waypoints'][0]['lon'] = $postData['longitude'];
	$ot_config_file['waypoints'][0]['rad'] = $postData['radius'];
	$ot_config_file['waypoints'][0]['desc'] = $postData['location'];
	$ot_config_file['waypoints'][0]['tst'] = time();
	LOGGING("Owntracks App configfile has been created", 7);
	//print_r($ot_config_file);
	$FileNameOT = LBPHTMLAUTHDIR."/files/OT_".$postData['name']."_".$postData['location']."_".$postData['radius']."_".date("Ymd").".otrc";
	//$Fname = $L['VALIDATION.SAVE_FILE']. " '".$postData['name']."_".$postData['location']."_".$postData['radius']."_".date("Ymd").".otrc' ".$L['VALIDATION.SAVE_FILE_WHERE'];
	//echo $FileNameOT;
	File_Put_Array_As_JSON($FileNameOT, $ot_config_file, $zip=false);
	$final_file_name = "OT_".$postData['name']."_".$postData['location']."_".$postData['radius']."_".date("Ymd").".otrc";
	LOGGING("Owntracks App configfile has been saved to data folder", 5);
	//return $ot_config_file;
	//print_r($FileNameOT);
	return($final_file_name);
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
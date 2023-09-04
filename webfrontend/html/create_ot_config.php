<?php

##############################################################################################################################
#
# Version: 	1.0.2
# Datum: 	25.08.2032
# veröffentlicht in: https://github.com/Liver64/LoxBerry-Owntracks/releases
# 
##############################################################################################################################

header('Content-Type: text/html; charset=utf-8');

# Includes
require_once "loxberry_system.php";
require_once "loxberry_log.php";
require_once "loxberry_io.php";
require_once "phpMQTT/phpMQTT.php";
include "system/error_handler.php";
require_once("system/Helper.php");
require_once("system/logging.php");

error_reporting(E_ALL);
ini_set("display_errors", "off");
define('ERROR_LOG_FILE', "$lbplogdir/owntracks.log");

# calling custom error handler
set_error_handler("handleError");

ini_set('max_execution_time', 60); 			// Max. Skriptlaufzeit auf 60 Sekunden
date_default_timezone_set(date("e"));		// setze korrekte Zeitzone
register_shutdown_function('shutdown');

# declare variables/constants
$ot_template_file = $lbpdatadir."/config_template.otrc";
$config_file = $lbpconfigdir."/owntracks.cfg";
$user_app_dir = $lbpdatadir."/user_config_files/";

echo '<PRE>';

$params = [	"name" => "Owntracks PHP",
			"filename" => "$lbplogdir/owntracks.log",
			"append" => 1,
			"addtime" => 1,
			];
$log = LBLog::newLog($params);

LOGSTART("PHP started");

# load Plugin Configuration
if (!is_file($config_file)) {
	LOGWARN('The file owntracks.cfg could not be opened, please try again!');
} else {
	$config = parse_ini_file($config_file, TRUE);
	if ($config === false)  {
		LOGERR('The file owntracks.cfg could not be parsed, the file may be disruppted. Please check/save your Plugin Config or check file "owntracks.cfg" manually!');
		exit(1);
	}
	LOGDEB("Owntracks config has been loaded");
}
$userid = ($config['USER']);
foreach ($userid as $type => $key) {
	$userarr[$type] = explode(',', $key[0]);
} 
$config['USER'] = $userarr;
LOGDEB("Owntracks is ready for usage");
#print_r($config);

if (!is_dir($user_app_dir))  {
	mkdir($lbpdatadir."/user_config_files");
	LOGDEB("User App config directory created");
}

$credentials = mqtt_connectiondetails();
$ot_config_file = read_tmpl_config_file($ot_template_file);
$FileNameOT = prepare_config_file($ot_config_file, $credentials);

# read config template file
function read_tmpl_config_file($FileName)  {
	
	$ot_config_file = json_decode(file_get_contents($FileName), TRUE);
	LOGDEB("Owntracks App template file has been loaded");
	return $ot_config_file;
}

# prepare and save OT config files
function prepare_config_file($ot_config_file, $credentials)  {
	
	global $config;

	foreach ($config['USER'] as $key => $value)    {

		$ot_config_file['host'] = $config['CONNECTION']['dyndns'];
		$ot_config_file['port'] = $config['CONNECTION']['port'];
		$ot_config_file['username'] = $credentials['brokeruser'];
		$ot_config_file['password'] = $credentials['brokerpass'];
		$ot_config_file['waypoints'][0]['lat'] = $config['LOCATION']['latitude'];
		#$ot_config_file['waypoints'][0]['rid'] = "";
		$ot_config_file['waypoints'][0]['lon'] = $config['LOCATION']['longitude'];
		$ot_config_file['waypoints'][0]['rad'] = $config['LOCATION']['radius'];
		$ot_config_file['waypoints'][0]['tst'] = time();
		$ot_config_file['deviceId'] = $key;
		if (empty($value[0]))   {
			$ot_config_file['waypoints'][0]['desc'] = $config['LOCATION']['location'];
			$ot_config_file['waypoints'][0]['rad'] = $config['LOCATION']['radius'];
		} else {
			$ot_config_file['waypoints'][0]['desc'] = $config['LOCATION']['location'].":".$value[0].":".$value[1].":".$value[2];
			$ot_config_file['waypoints'][0]['rad'] = '0';
		}
		LOGDEB("Owntracks App config file for '".$key."' has been prepared.");
		//$FileNameOT = LBPHTMLAUTHDIR."/user_config_files/OT_".$key."_".$config['LOCATION']['location']."_".$config['LOCATION']['radius']."_".date("Ymd").".otrc";
		$FileNameOTName = LBPDATADIR."/user_config_files/".$key.".otrc";
		//file_put_contents($FileNameOT, json_encode($ot_config_file, JSON_PRETTY_PRINT));
		file_put_contents($FileNameOTName, json_encode($ot_config_file, JSON_PRETTY_PRINT));
		//$final_file_name = "OT_".$key."_".$config['LOCATION']['location']."_".$config['LOCATION']['radius']."_".date("Ymd").".otrc";
		LOGOK("Owntracks App config file for '".$key."' has been saved to folder");
		print_r($ot_config_file);
	}
}

function shutdown()
{
	global $log;
	$log->LOGEND("PHP finished");
}
?>
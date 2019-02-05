<?php
/**
* Submodul: logging
*
**/

/**
* Function : logging --> provide interface to LoxBerry logfile
*
* @param: 	empty
* @return: 	log entry
**/

function LOGGING($message = "", $loglevel = 7, $raw = 0)
{
	global $pcfg, $L, $config, $lbplogdir, $logfile, $plugindata;

	if ($plugindata['PLUGINDB_LOGLEVEL'] >= intval($loglevel) || $loglevel == 8)  {
		($raw == 1)?$message="<br>".$message:$message=htmlentities($message);
		switch ($loglevel) 	{
		    case 0:
		        #LOGEMERGE("$message");
		        break;
		    case 1:
		        LOGALERT("$message");
		        break;
		    case 2:
		        LOGCRIT("$message");
		        break;
			case 3:
		        LOGERR("$message");
		        break;
			case 4:
				LOGWARN("$message");
		        break;
			case 5:
				LOGOK("$message");
		        break;
			case 6:
				LOGINF("$message");
		        break;
			case 7:
				LOGDEB("$message");
			default:
		        break;
		}
		if ($loglevel < 4) {
			if (isset($message) && $message != "" ) notify (LBPPLUGINDIR, $L['BASIC.MAIN_TITLE'], $message);
		}
	}
	return;
}

?>

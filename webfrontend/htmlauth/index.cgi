#!/usr/bin/perl -w


##########################################################################
# Modules required
##########################################################################

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use LoxBerry::Storage;
use LoxBerry::IO;
use LoxBerry::JSON;

use CGI;
use CGI qw( :standard);
use File::Copy qw(copy);
use LWP::Simple;
use JSON qw( decode_json );
use utf8;

#use warnings;
#use strict;
#no strict "refs"; # we need it for template system

##########################################################################
# Generic exception handler
##########################################################################

# Every non-handled exceptions sets the @reason variable that can
# be written to the logfile in the END function

$SIG{__DIE__} = sub { our @reason = @_ };

##########################################################################
# Variables
##########################################################################

my $template_title;
my $saveformdata = 0;
my $do = "form";
my $helptemplate;
our $content;
our $template;
our %navbar;
our $pid;
our $change;
our $mqtt_host;
our $mqtt_pass;
our $mqtt_account;
our $otport;
our $mqttcred;
our $lbv;
our $trackstatus;
our $savedtrack;
our $countuser;
our $countappuser;

my $ip 							= LoxBerry::System::get_localip();
my $helptemplatefilename		= "help.html";
my $languagefile 				= "owntracks.ini";
my $maintemplatefilename	 	= "owntracks.html";
my $errortemplatefilename 		= "error.html";
my $pluginconfigfile 			= "owntracks.cfg";
my $recorderhttpport 			= "8083";
my $pluginlogfile				= "owntracks.log";
our $log 						= LoxBerry::Log->new ( name => 'Owntracks UI', filename => $lbplogdir ."/". $pluginlogfile, append => 1, addtime => 1 );
my $helplink 					= "https://www.loxwiki.eu/display/LOXBERRY/Owntracks";
my $pcfg 						= new Config::Simple($lbpconfigdir . "/" . $pluginconfigfile);
our $error_message				= "";
our $ot_message					= "";


##########################################################################
# Set new config options for upgrade installations
##########################################################################

# add new parameter for migration
if (!defined $pcfg->param("CONNECTION.mig")) {
	$pcfg->param("CONNECTION.mig", "");
	$pcfg->save() or &error;
} 

##########################################################################
# Read Settings
##########################################################################

# read language
my $lblang = lblanguage();

# Read Plugin Version
my $sversion = LoxBerry::System::pluginversion();

# Read LoxBerry Version
my $lbversion = LoxBerry::System::lbversion();

# IP-Address
my $myip =  LoxBerry::System::get_localip();

# Get MQTT Credentials
$mqttcred = LoxBerry::IO::mqtt_connectiondetails();

# read all POST-Parameter in namespace "R".
our $cgi = CGI->new;
$cgi->import_names('R');

$lbv = substr($lbversion,0,1);


#########################################################################
## Handle all ajax requests 
#########################################################################

our $q = $cgi->Vars;
#my $saveformdata = $q->{saveformdata};

my %pids;


if( $q->{ajax} ) 
{
	my %response;
		
	ajax_header();
	if( $q->{ajax} eq "getpids" ) {
		pids();
		$response{pids} = \%pids;
		print JSON::encode_json(\%response);
	}
	if( $q->{ajax} eq "restartrecorder" ) {
		`cd $lbpbindir ; $lbpbindir/restart.sh > /dev/null 2>&1 &`;
		pids();
		$response{pids} = \%pids;
		print JSON::encode_json(\%response);
	}
	if( $q->{ajax} eq "recorderconfig" ) {
		&recorder_config;
	}
	exit;
}



# Everything from Forms
LOGSTART "Owntracks UI started";


#########################################################################
# Parameter
#########################################################################

$saveformdata = defined $R::saveformdata ? $R::saveformdata : undef;
$do = defined $R::do ? $R::do : "form";

##########################################################################
# Set LoxBerry SDK to debug in plugin 
##########################################################################

if($log->loglevel() eq "7") {
	$LoxBerry::System::DEBUG 	= 1;
	$LoxBerry::Web::DEBUG 		= 1;
	$LoxBerry::Log::DEBUG		= 1;
}

##########################################################################
# Template preparation
##########################################################################

# preparing error template;
my $errortemplate = HTML::Template->new(
					filename => $lbptemplatedir . "/" . $errortemplatefilename,
					global_vars => 1,
					loop_context_vars => 1,
					die_on_bad_params=> 0,
					associate => $cgi,
					%htmltemplate_options,
					debug => 1,
					);
my %ERR = LoxBerry::System::readlanguage($errortemplate, $languagefile);

# übergibt Log Verzeichnis und Dateiname an HTML
#$template->param("LOGFILE" , $lbplogdir . "/" . $pluginlogfile);

##########################################################################
# Check Config file
##########################################################################

if (!-r $lbpconfigdir . "/" . $pluginconfigfile) 
{
	LOGCRIT "Plugin config file does not exist";
	$error_message = $ERR{'ERRORS.ERR_CHECK_CONFIG_FILE'};
	&error; 
} else {
	LOGDEB "The Plugin config file has been loaded";
}


##########################################################################
# Check if MQTT Plugin is installed
##########################################################################

#my $mqtt = $lbhomedir . "/config/plugins/mqttgateway/mqtt.json";
if (!$mqttcred) 
{
	LOGCRIT "It seems that MQTT Plugin is not installed";
	$error_message = $ERR{'ERRORS.ERR_CHECK_MQTT_PLUGIN'};
	&error; 
} else {
	LOGINF "MQTT Plugin is installed";
}


##########################################################################
# Initiate Main Template
##########################################################################
inittemplate();


##########################################################################
# Some Settings
##########################################################################

$template->param("LBADR", lbhostname().":".lbwebserverport());
#$template->param("LBADR", $myip.":".lbwebserverport());
$template->param("PLUGINDIR" => $lbpplugindir);

LOGDEB "Read main settings from " . $languagefile . " for language: " . $lblang;


##########################################################################
# check if weather4lox is installed and parse data
##########################################################################

# Check if weather4lox.cfg file exist and parse in
if ($pcfg->param("LOCATION.longitude") eq '' or $pcfg->param("LOCATION.latitude") eq '')  
{
	if (-r $lbhomedir . "/config/plugins/weather4lox/weather4lox.cfg") 
	{
		my $wcfg = new Config::Simple($lbhomedir . "/config/plugins/weather4lox/weather4lox.cfg");
		LOGDEB "Weather4lox Plugin has been detected and config file has been loaded";
		# import longitude
		if (!$wcfg->param("DARKSKY.COORDLONG") eq "")   {
			$pcfg->param("LOCATION.longitude", $wcfg->param("DARKSKY.COORDLONG"));
			LOGDEB "Longitude has been passed over from weather4lox Darksky settings";
		} elsif (!$wcfg->param("WEATHERBIT.COORDLONG") eq "")   {
			$pcfg->param("LOCATION.longitude", $wcfg->param("WEATHERBIT.COORDLONG"));
			LOGDEB "Longitude has been passed over from weather4lox Weatherbit settings";
		} elsif (!$wcfg->param("WUNDERGROUND.COORDLONG") eq "")   {
			$pcfg->param("LOCATION.longitude", $wcfg->param("WUNDERGROUND.COORDLONG"));
			LOGDEB "Longitude has been passed over from weather4lox Wunderground settings";
		}
		# import latitude
		if (!$wcfg->param("DARKSKY.COORDLAT") eq "")   {
			$pcfg->param("LOCATION.latitude", $wcfg->param("DARKSKY.COORDLAT"));
			LOGDEB "Latitude has been passed over from weather4lox Darksky settings";
		} elsif (!$wcfg->param("WEATHERBIT.COORDLAT") eq "")   {
			$pcfg->param("LOCATION.latitude", $wcfg->param("WEATHERBIT.COORDLAT"));
			LOGDEB "Latitude has been passed over from weather4lox Weatherbit settings";
		} elsif (!$wcfg->param("WUNDERGROUND.COORDLAT") eq "")   {
			$pcfg->param("LOCATION.latitude", $wcfg->param("WUNDERGROUND.COORDLAT"));
			LOGDEB "Latitude has been passed over from weather4lox Wunderground settings";
		}
		$template->param("locationdata" => 1);
		$pcfg->param("LOCATION.locationdata" => 1);
		$pcfg->save() or &error;
		LOGDEB "Data from weather4lox has been saved";
	} else {
		LOGDEB "No Geo location data found on your LoxBerry";
	}
	
} else {
	$template->param("locationdata" => 1);
	LOGDEB "Location data used from Plugin config";
}


##########################################################################
# Main program
##########################################################################

	# get MQTT Credentials
	if ($mqttcred)   {
		$mqtt_account = $mqttcred->{brokeruser};
		$mqtt_pass = $mqttcred->{brokerpass};
		LOGDEB "MQTT credentials obtained";
	}
	
	# get MQTT Config
	if ($mqttcred)   {
		$mqtt_host = $mqttcred->{brokeraddress};
		LOGDEB "MQTT hostname obtained";
	}
	
	# check if migration to be executed or fresh installation
	my $old_folder = $lbphtmlauthdir."/files/";
	
	if ($pcfg->param("CONNECTION.mig") ne "completed")  {
		#if (-d $old_folder)  {
			&migrate_user;
			exit;
		#}
	}
	
	# Navbar
	$navbar{10}{Name} = "$SL{'BASIC.NAVBAR_FIRST'}";
	$navbar{10}{URL} = './index.cgi';

	if ($pcfg->param("LOCATION.longitude") eq '' or $pcfg->param("LOCATION.latitude") eq '')  
	{
		$navbar{20}{Name} = "$SL{'BASIC.NAVBAR_SECOND'}";
		$navbar{20}{URL} = 'https://www.google.com/maps';
		$navbar{20}{target} = '_blank';
	}

	$navbar{30}{Name} = "$SL{'BASIC.NAVBAR_THIRD'}";
	$navbar{30}{URL} = './index.cgi?do=command';

	my $track = $pcfg->param("CONNECTION.track");
	if (is_enabled($track))  {
		$navbar{40}{Name} = "$SL{'BASIC.NAVBAR_FOURTH'}";
		$navbar{40}{URL} = 'http://'.$myip.':'.$recorderhttpport;
		$navbar{40}{target} = '_blank';
	}

	if($mqttcred and $lbv < 3)  {
		$navbar{50}{Name} = "$SL{'BASIC.NAVBAR_SIXTH'}";
		$navbar{50}{URL} = '/admin/plugins/mqttgateway/index.cgi';
		$navbar{50}{target} = '_blank';
	} else {
		$navbar{50}{Name} = "$SL{'BASIC.NAVBAR_SIXTH'}";
		$navbar{50}{URL} = '/admin/system/mqtt.cgi';
		$navbar{50}{target} = '_blank';
	}
	
	$navbar{90}{Name} = "$SL{'BASIC.NAVBAR_FIVETH'}";
	$navbar{90}{URL} = './index.cgi?do=logfiles';

if ($R::saveformdata) {
	$template->param( FORMNO => 'form' );
	&save;
}

if(!defined $do or $do eq "form") {
	$navbar{10}{active} = 1;
	$template->param("FORM", "1");
	&form;
} elsif ($do eq "tracking") {
	$navbar{40}{active} = 1;
	printtemplate();
} elsif ($do eq "command") {
	$navbar{30}{active} = 1;
	$template->param("COMMAND", "1");
	&topics_form;
} elsif ($do eq "restarttracking") {
	&print_track;
} elsif ($do eq "logfiles") {
	LOGTITLE "Show logfiles";
	$navbar{90}{active} = 1;
	$template->param("LOGFILES", "1");
	$template->param("LOGLIST_HTML", LoxBerry::Web::loglist_html());
	printtemplate();
}
$error_message = "Invalid do parameter: ".$do;
&error;
exit;



#####################################################
# Form-Sub
#####################################################

sub form 
{	
	# User einlesen
	our $countuser = 0;
	our $rowsuser;
	my $UUID;
	my $major;
	my $minor;
	
	my %userconfig = $pcfg->vars();	
	foreach my $key (keys %userconfig) {
		if ( $key =~ /^USER/ ) {
			$countuser++;
			my $user = $key;
			$user =~ s/^USER\.//g;
			$user =~ s/\[\]$//g;
			my @fields = $pcfg->param($key);
			$rowsuser .= "<tr><td style='width: 4%;'><INPUT type='checkbox' style='width: 100%' name='chkuser$countuser' id='chkuser$countuser' align='left'/></td>\n";
			$rowsuser .= "<td style='width: 22%'><input id='username$countuser' name='username$countuser' type='text' class='uname' placeholder='$SL{'MENU.USER_LISTING'}' value='$user' align='left' data-validation-error-msg='$SL{'VALIDATION.USER_NAME'}' data-validation-rule='^([äöüÖÜßÄ A-Za-z0-9\ ]){1,20}' style='width: 100%;'></td>\n";
			#$rowsuser .= "<td style='width: 4%'><a name='create$countuser' id='create$countuser' class='createconfbutton' data-auto-download data-role='button' data-inline='true' data-mini='true' data-icon='check'>$SL{'BUTTON.NEW_CONFIG'}</a></td>\n";
			$rowsuser .= "<td style='width: 25%'><input name='UUID$countuser' id='UUID$countuser' class='uuid' placeholder='iBeacon UUID' type='text' value='$fields[0]' data-validation-rule='[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[34][0-9a-fA-F]{3}-[89ab][0-9a-fA-F]{3}-[0-9a-fA-F]{12}' data-validation-error-msg='$SL{'VALIDATION.UUID'}'></td>\n";
			$rowsuser .= "<td style='width: 5%'><input name='uuidmajor$countuser' id='uuidmajor$countuser' class='uuid' placeholder='Major' type='text' value='$fields[1]' data-validation-rule='special:port' data-validation-error-msg='$SL{'VALIDATION.UUID_MAJOR'}'></td>\n";
			$rowsuser .= "<td style='width: 5%'><input name='uuidminor$countuser' id='uuidminor$countuser' class='uuid' placeholder='Minor' type='text' value='$fields[2]' data-validation-rule='special:port' data-validation-error-msg='$SL{'VALIDATION.UUID_MINOR'}'></td>\n";			
			
			my $filecheck = "/var/spool/owntracks/recorder/store/last/loxberry/".lc($user)."/loxberry-".lc($user).".json";
			
			my $filecreationcheck = "$lbpdatadir/user_config_files/$user.otrc";
						
			# check if actual data been recieved
			if (-r $filecheck) {
				$rowsuser .= "<td style='width: 2%'><img class='picture' src='/plugins/$lbpplugindir/images/green.png' id='tra$countuser' name='tra$countuser'></td>\n";
				$rowsuser .= "<td style='width: 80%'><div id='response$countuser'></div></td>\n";
				next;
			} 
			# check if App config file exists
			if (!-r $filecreationcheck) {
				$rowsuser .= "<td style='width: 2%'><img class='picture' src='/plugins/$lbpplugindir/images/red.png' id='tra$countuser' name='tra$countuser'></td>\n";
			} else {
				$rowsuser .= "<td style='width: 2%'><img class='picture' src='/plugins/$lbpplugindir/images/yellow.png' id='tra$countuser' name='tra$countuser'></td>\n";
			}
			$rowsuser .= "<td style='width: 80%'><div id='response$countuser'></div></td>\n";
		}
	}

	if ( $countuser < 1 ) {
		$rowsuser .= "<tr><td colspan=6>" . $SL{'VALIDATION.USER_EMPTY'} . "</td></tr>\n";
	}
	LOGDEB "$countuser User has been loaded.";
	$rowsuser .= "<input type='hidden' id='countuser' name='countuser' value='$countuser'>\n";
	$template->param("ROWSUSER", $rowsuser);
		
	&printtemplate;
	exit;
	
	#$content = $filecreationcheck;
	#print_test($content);
	#exit;
}



#####################################################
# Save-Sub
#####################################################

sub save 
{
	# Everything from Forms
	my $i;
	my $countuser = "$R::countuser";
			
	# OK - now installing...
		
	$trackstatus = $R::track;
	$savedtrack = $pcfg->param("CONNECTION.track");
	
	if ($trackstatus eq "true")  {
		&compare_config;
		if ($count > 1)  {
			$pcfg->param("RECORDER_HTTP.OTR_BROWSERAPIKEY", "$R::googleapikey");
			$pcfg->param("RECORDER_MQTT.OTR_USER", "$mqtt_account");
			$pcfg->param("RECORDER_MQTT.OTR_PASS", "$mqtt_pass");
			$pcfg->param("CONNECTION.track", "true");
			$pcfg->save() or &error;
			&recorder_config;
			LOGINF "MQTT config changed, new settings saved and recorder restarted";
		}
		if ($trackstatus ne $savedtrack)  {
			$pcfg->param("CONNECTION.track", "true");
			`cd $lbpbindir ; $lbpbindir/restart.sh > /dev/null 2>&1 &`;
			system("/bin/sh $lbpbindir/restart.sh");
			unlink $lbpconfigdir."/ot-recorder";
			LOGDEB "Tracking change saved, Recorder restarted";

		}
	} else {
		$pcfg->param("CONNECTION.track", "false");
		system("sudo systemctl stop ot-recorder");
		LOGDEB "Recorder stopped";
	}
	LOGINF "Start writing Plugin config file";
	# turn on if TLS works
	#$pcfg->param("CONNECTION.tls", "$R::tls");
	$pcfg->param("LOCATION.location", "$R::location");
	$pcfg->param("LOCATION.radius", "$R::radius");
	$pcfg->param("LOCATION.latitude", "$R::latitude");
	$pcfg->param("LOCATION.longitude", "$R::longitude");
	$pcfg->param("CONNECTION.dyndns", "$R::dyndns");
	$pcfg->param("CONNECTION.port", "$R::port");
	
	# save all user
	for ($i = 1; $i <= $countuser; $i++) {
		my $username = param("username$i");
		if ( param("chkuser$i") ) { # if user should be deleted
			$pcfg->delete( "USER." . $username . "[]" );
			unlink("$lbpdatadir/user_config_files/$username.otrc");
		} else { # save
			my $UUID = param("UUID$i");
			my $uuidmajor = param("uuidmajor$i");
			my $uuidminor = param("uuidminor$i");
			$pcfg->param( "USER." . $username . "[]",  $UUID . "," . $uuidmajor  . "," . $uuidminor);
		}
	}
	$pcfg->save() or &error;
	LOGOK "All settings has been saved";
	
	# create User specific App configuration files
	my $file = qx(/usr/bin/php $lbphtmldir/create_ot_config.php);	

	&print_save;
	exit;
	
	#$content = param("USER$i");
	#print_test($content);
	#exit;
}


#####################################################
# Sub compare_config
#####################################################

sub compare_config 
{	
	$count = 1;
	
	# compare config in order to check if recorder require updates
	my $saved_track = $pcfg->param("CONNECTION.track");
	my $saved_mqtt_user = $pcfg->param("RECORDER_MQTT.OTR_USER");
	my $saved_mqtt_pass = $pcfg->param("RECORDER_MQTT.OTR_PASS");
	my $saved_mqtt_api = $pcfg->param("RECORDER_HTTP.OTR_BROWSERAPIKEY");
	
	if ($mqtt_account ne $saved_mqtt_user)  {
			$count++;
	}
	if ($mqtt_pass ne $saved_mqtt_pass)  {
			$count++;
	}
	if ($R::googleapikey ne $saved_mqtt_api)  {
			$count++;
	}
	LOGDEB "MQTT config different, Plugin will be updated";
	return;
}

#####################################################
# Sub Recorder Configuration
#####################################################

sub recorder_config 
{	
	my $mqtt_account = $mqttcred->{brokeruser};
	my $mqtt_pass = $mqttcred->{brokerpass};
	my $file = $lbpdatadir."/ot-recorder.txt";

	# Use the open() function to create the file.
	unless(open FILE, '>'.$file) {
		# Die with error message 
		# if we can't open it.
		LOGCRIT "\nUnable to create $file\n";
	}
	$otport = $pcfg->param("CONNECTION.port");

	# Write some text to the file.
	print FILE "OTR_STORAGEDIR=\"/var/spool/owntracks/recorder/store\"\n";
	print FILE "OTR_HOST=\"localhost\"\n";
	print FILE "OTR_PORT=\"1883\"\n";
	print FILE "OTR_USER=\"$mqtt_account\"\n";
	print FILE "OTR_PASS=\"$mqtt_pass\"\n";
	print FILE "OTR_HTTPHOST=\"$myip\"\n";
	print FILE "OTR_HTTPPORT=\"$recorderhttpport\"\n";
	print FILE "OTR_BROWSERAPIKEY=\"$R::googleapikey\"\n";
	print FILE "OTR_TOPICS=\"owntracks/# owntracks/+/+\"\n";

	# close the file.
	close FILE;

	# copy newly created file to destination
	my $savefile = $lbpconfigdir."/ot-recorder";
	my $finalfile = "/etc/default/ot-recorder";
	rename $file, $lbpconfigdir."/ot-recorder";
	copy $savefile, $finalfile;
	LOGOK "Recorder config file saved to /etc/default/ot-recorder";
	
	if ($trackstatus eq "true")  {
		$pcfg->param("CONNECTION.track", "true");
		`cd $lbpbindir ; $lbpbindir/restart.sh > /dev/null 2>&1 &`;
		system("/bin/sh $lbpbindir/restart.sh");
		unlink $lbpconfigdir."/ot-recorder";
		$pcfg->save() or &error;
		LOGINF "Tracking change saved, Recorder restarted";
	}
	$ot_message = $SL{'SAVE.SAVE_OT'};
	return;
}


#####################################################
# Sub migrate User accounts
#####################################################

sub migrate_user()
{	
	my $old_folder = $lbphtmlauthdir."/files/user_app/";
	$countappuser = 10;
	
	if (!-d $lbpdatadir."/user_config_files") {
		mkdir($lbpdatadir."/user_config_files");
		LOGDEB "Directory '$lbpdatadir/user_config_files' has been created";
	}
	
	# Migrate
	for ($i = 1; $i <= $countappuser; $i++) {
		my $userid = $pcfg->param("USER$i.name");
		if ($userid ne '')  {
			$pcfg->param("USER." . $userid . "[]", "");
			LOGOK "Migration: USER$i=$old_user has been migrated";
		}
	}
	
	# delete
	for ($i = 1; $i <= $countappuser; $i++) {
	if ($pcfg->param("USER$i.name") ne '')  {
			$pcfg->delete("USER$i.name");
			$pcfg->delete("USER$i");
			LOGOK "Deletion: USER$i.name has been deleted";
		}
	}
	$pcfg->param("CONNECTION.mig", "completed");	
	$pcfg->delete("CONNECTION.migration");
	$pcfg->save() or &error;
	unlink glob $lbphtmlauthdir."/files/user_app/*.*";
	rmdir( $lbphtmlauthdir."/files/user_app/");
	rmdir( $lbphtmlauthdir."/files/");
	LOGOK "Migration saved and completed";
	#LOGINF "Move off files has been called";
	#my $filemove = qx(/usr/bin/php $lbphtmldir/migration_app_files.php);
	LOGOK "All old files has been deleted";
	&print_migration;
	exit;
}

########################################################################
# Topics Form 
########################################################################
sub topics_form
{
	require POSIX;
	
	my $datafile = "/dev/shm/mqttgateway_topics.json";
	my $relayjsonobj = LoxBerry::JSON->new();
	my $relayjson = $relayjsonobj->open(filename => $datafile);
	my $http_table;
	my $http_count;
	my $udp_count;
	my $udp_table;
	my $topic;
	
		
	# HTTP
	$http_count = 0;
	$http_table .= qq { <table class="topics_table_http" id="http_table" name="http_table" data-filter-reveal="true" data-filter-placeholder="$SL{'VALIDATION.SEARCH'}" data-filter="true"> };
	$http_table .= qq { <thead> };
	$http_table .= qq { <tr> };
	$http_table .= qq { <th>Miniserver Virtual Input</th> };
	$http_table .= qq { <th>Last value</th> };
	$http_table .= qq { <th>Last submission</th> };
	$http_table .= qq { </tr> };
	$http_table .= qq { </thead> };
	$http_table .= qq { <tbody> };
	
	foreach $topic (sort keys %{$relayjson->{http}}) {
		$http_count++;
		$http_table .= qq { <tr> };
		$http_table .= qq { <td><font color="blue">$topic</font></td> };
		$http_table .= qq { <td>$relayjson->{http}{$topic}{message}</td> };
		$http_table .= qq { <td> } . POSIX::strftime('%d.%m.%Y %H:%M:%S', localtime($relayjson->{http}{$topic}{timestamp})) . qq { </td> };
		$http_table .= qq { </tr> };
	}
	$http_table .= qq { </tbody> };
	$http_table .= qq { </table> };
	
	$template->param("http_table", $http_table);
	#$template->param("http_count", $http_count);
	
	
	# UDP
	$udp_count = 0;
	$udp_table .= qq { <table class="topics_table_udp" id="udp_table" name="udp_table" data-filter-reveal="true" data-filter-placeholder="$SL{'VALIDATION.SEARCH'}" data-filter="true"> };
	$udp_table .= qq { <thead> };
	$udp_table .= qq { <tr> };
	$udp_table .= qq { <th>Miniserver UDP</th> };
	$udp_table .= qq { <th>Last value</th> };
	$udp_table .= qq { <th>Last submission</th> };
	$udp_table .= qq { </tr> };
	$udp_table .= qq { </thead> };
	$udp_table .= qq { <tbody> };
	
	foreach $topic (sort keys %{$relayjson->{udp}}) {
		$udp_count++;
		$udp_table .= qq { <tr> };
		$udp_table .= qq { <td><font color="blue">$topic=$relayjson->{udp}{$topic}{message}</font></td> };
		$udp_table .= qq { <td>$relayjson->{udp}{$topic}{message}</td> };
		$udp_table .= qq { <td> } . POSIX::strftime('%d.%m.%Y %H:%M:%S', localtime($relayjson->{udp}{$topic}{timestamp})) . qq { </td> };
		$udp_table .= qq { </tr> };
	}
	$udp_table .= qq { </tbody> };
	$udp_table .= qq { </table> };
	
	$template->param("udp_table", $udp_table);
	#$template->param("udp_count", $udp_count);
	
	printtemplate();
	exit;
	
}


######################################################################
# AJAX functions
######################################################################

sub pids 
{
	$pids{'recorder'} = (split(" ",`ps -A | grep \"ot-recorder\"`))[0];
	$pids{'mqttgateway'} = trim(`pgrep mqttgateway.pl`) ;
	$pids{'mosquitto'} = trim(`pgrep mosquitto`) ;
	#LOGDEB "PIDs updated";
}	

sub ajax_header
{
	print $cgi->header(
			-type => 'application/json',
			-charset => 'utf-8',
			-status => '200 OK',
	);	
	#LOGOK "AJAX posting received and processed";
}	



#####################################################
# Error-Sub
#####################################################

sub error 
{
	$template_title = $ERR{'BASIC.MAIN_TITLE'} . ": v$sversion - " . $ERR{'BUTTON.ERR_TITLE'};
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	$errortemplate->param('ERR_MESSAGE'		, $error_message);
	$errortemplate->param('ERR_TITLE'		, $ERR{'BUTTON.ERR_TITLE'});
	$errortemplate->param('ERR_BUTTON_BACK' , $ERR{'BUTTON.ERR_BUTTON_BACK'});
	$errortemplate->param('ERR_NEXTURL'	, $ENV{REQUEST_URI});
	print $errortemplate->output();
	LoxBerry::Web::lbfooter();
	exit;
}


#####################################################
# Save
#####################################################

sub print_save
{
	$template->param("SAVE", "1");
	$template_title = "$SL{'BASIC.MAIN_TITLE'}: v$sversion";
	$template->param('OT_MESSAGE', $ot_message);
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}


#####################################################
# Attention Tracking
#####################################################

sub print_track
{
	$template->param("TRACK", "1");	
	$template_title = "$SL{'BASIC.MAIN_TITLE'}: v$sversion";
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}

#####################################################
# Print Migration
#####################################################

sub print_migration
{
	$template->param("MIGRATION", "1");	
	$template_title = "$SL{'BASIC.MAIN_TITLE'}: v$sversion";
	LoxBerry::Web::lbheader($template_title, $helplink, $helptemplatefilename);
	print $template->output();
	LoxBerry::Web::lbfooter();
	exit;
}

##########################################################################
# Init Template
##########################################################################

sub inittemplate
{
	$template =  HTML::Template->new(
				filename => $lbptemplatedir . "/" . $maintemplatefilename,
				global_vars => 1,
				loop_context_vars => 1,
				die_on_bad_params=> 0,
				associate => $pcfg,
				%htmltemplate_options,
				debug => 1,
				cache => 0,
				);
	%SL = LoxBerry::System::readlanguage($template, $languagefile);			

}


##########################################################################
# Print Template
##########################################################################

sub printtemplate
{
	# Print Template
	$template_title = "$SL{'BASIC.MAIN_TITLE'}: v$sversion";
	LoxBerry::Web::head();
	LoxBerry::Web::pagestart($template_title, $helplink, $helptemplate);
	print LoxBerry::Log::get_notifications_html($lbpplugindir);
	print $template->output();
	LoxBerry::Web::lbfooter();
	LOGOK "Website printed";
	exit;
}


##########################################################################
# Print for testing
##########################################################################

sub print_test
{	
	use Data::Dumper;
	
	# Print Template
	print "Content-Type: text/html; charset=utf-8\n\n"; 
	print "*********************************************************************************************";
	print "<br>";
	print " *** Ausgabe zu Testzwecken";
	print "<br>";
	print "*********************************************************************************************";
	print "<br>";
	print "<br>";
	print Dumper($content);
	#print $content;

	exit;
}


##########################################################################
# END routine - is called on every exit (also on exceptions)
##########################################################################
sub END 
{	
	our @reason;
	
	if ($log) {
		if (@reason) {
			LOGCRIT "Unhandled exception catched:";
			LOGERR @reason;
			LOGEND "Finished with an exception";
		} elsif ($error_message) {
			LOGEND "Finished with error: ".$error_message;
		} else {
			#LOGEND "Finished successful";
		}
	}
}
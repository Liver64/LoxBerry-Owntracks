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
		} elsif (!$wcfg->param("WEATHERFLOW.COORDLONG") eq "")   {
			$pcfg->param("LOCATION.longitude", $wcfg->param("WEATHERFLOW.COORDLONG"));
			LOGDEB "Longitude has been passed over from weatherflow Wunderground settings";
		} elsif (!$wcfg->param("OPENWEATHER.COORDLONG") eq "")   {
			$pcfg->param("LOCATION.longitude", $wcfg->param("OPENWEATHER.COORDLONG"));
			LOGDEB "Longitude has been passed over from openweather Wunderground settings";
		} elsif (!$wcfg->param("VISUALCROSSING.COORDLONG") eq "")   {
			$pcfg->param("LOCATION.longitude", $wcfg->param("VISUALCROSSING.COORDLONG"));
			LOGDEB "Longitude has been passed over from visualcrossing Wunderground settings";
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
		} elsif (!$wcfg->param("WEATHERFLOW.COORDLAT") eq "")   {
			$pcfg->param("LOCATION.latitude", $wcfg->param("WEATHERFLOW.COORDLAT"));
			LOGDEB "Latitude has been passed over from weatherflow Wunderground settings";
		} elsif (!$wcfg->param("OPENWEATHER.COORDLAT") eq "")   {
			$pcfg->param("LOCATION.latitude", $wcfg->param("OPENWEATHER.COORDLAT"));
			LOGDEB "Latitude has been passed over from openweather Wunderground settings";
		} elsif (!$wcfg->param("VISUALCROSSING.COORDLAT") eq "")   {
			$pcfg->param("LOCATION.latitude", $wcfg->param("VISUALCROSSING.COORDLAT"));
			LOGDEB "Latitude has been passed over from visualcrossing Wunderground settings";
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
		if (-d $old_folder)  {
			&migrate_user;
			exit;
		}
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
	my $i;
	my $countuser = "$R::countuser";

	LOGINF "Start writing Plugin config file";

	# Track state
	$trackstatus = _val($R::track);
	$savedtrack  = _val($pcfg->param("CONNECTION.track"));

	# 1) Check if recorder relevant settings changed (before overwriting pcfg)
	my $need_rec_update = recorder_needs_update();

	# 2) Save normal plugin settings
	$pcfg->param("LOCATION.location",   _val($R::location));
	$pcfg->param("LOCATION.radius",     _val($R::radius));
	$pcfg->param("LOCATION.latitude",   _val($R::latitude));
	$pcfg->param("LOCATION.longitude",  _val($R::longitude));
	$pcfg->param("CONNECTION.dyndns",   _val($R::dyndns));
	$pcfg->param("CONNECTION.port",     _val($R::port));

	# If tracking enabled, also store recorder-related keys in config
	if ($trackstatus eq "true") {
		$pcfg->param("RECORDER_HTTP.OTR_BROWSERAPIKEY", _val($R::googleapikey));
		$pcfg->param("RECORDER_MQTT.OTR_USER", _val($mqttcred->{brokeruser}));
		$pcfg->param("RECORDER_MQTT.OTR_PASS", _val($mqttcred->{brokerpass}));
		$pcfg->param("CONNECTION.track", "true");
	} else {
		$pcfg->param("CONNECTION.track", "false");
	}

	# save all user
	for ($i = 1; $i <= $countuser; $i++) {
		my $username = param("username$i");
		if (param("chkuser$i")) {
			$pcfg->delete("USER." . $username . "[]");
			unlink("$lbpdatadir/user_config_files/$username.otrc");
		} else {
			my $UUID      = param("UUID$i");
			my $uuidmajor = param("uuidmajor$i");
			my $uuidminor = param("uuidminor$i");
			$pcfg->param("USER." . $username . "[]", $UUID . "," . $uuidmajor . "," . $uuidminor);
		}
	}

	$pcfg->delete("CONNECTION.migration");
	$pcfg->save() or &error;
	LOGOK "All settings has been saved";

	# 3) Apply recorder update/restart logic
	if ($trackstatus eq "true") {

		# If tracking toggled from false->true OR recorder relevant settings changed
		if ($savedtrack ne "true" || $need_rec_update) {
			my $ok = recorder_config();   # writes /etc/default/ot-recorder
			if ($ok) {
				system("sudo systemctl restart ot-recorder");
				LOGINF "Recorder restarted (tracking enabled / config changed)";
			} else {
				LOGERR "Recorder config update failed - recorder not restarted";
			}
		}

	} else {
		# tracking disabled -> stop recorder only if it was enabled before, or always (your choice)
		system("sudo systemctl stop ot-recorder");
		LOGDEB "Recorder stopped";
	}

	# create User specific App configuration files
	my $file = qx(/usr/bin/php $lbphtmldir/create_ot_config.php);

	&print_save;
	exit;
}


#####################################################
# Sub compare_config
#####################################################

sub compare_config
{
	# backwards compatibility wrapper
	our $count;
	$count = recorder_needs_update() ? 2 : 1;
	return;
}


#####################################################
# Sub Recorder Configuration
#####################################################

sub recorder_config
{
	# nur Datei schreiben/kopieren (kein restart, kein pcfg->save)
	my $ok = write_recorder_default_file();
	$ot_message = $SL{'SAVE.SAVE_OT'};
	return $ok;
}

sub _val { defined $_[0] ? $_[0] : '' }

# Returns 1 if recorder-relevant settings changed, else 0
sub recorder_needs_update
{
	# NEW (Form/runtime)
	my $new_mqtt_user = _val($mqttcred->{brokeruser});
	my $new_mqtt_pass = _val($mqttcred->{brokerpass});
	my $new_api       = _val($R::googleapikey);

	my $new_location  = _val($R::location);
	my $new_radius    = _val($R::radius);
	my $new_lat       = _val($R::latitude);
	my $new_lon       = _val($R::longitude);

	my $new_dyndns    = _val($R::dyndns);
	my $new_port      = _val($R::port);

	# OLD (saved)
	my $old_mqtt_user = _val($pcfg->param("RECORDER_MQTT.OTR_USER"));
	my $old_mqtt_pass = _val($pcfg->param("RECORDER_MQTT.OTR_PASS"));
	my $old_api       = _val($pcfg->param("RECORDER_HTTP.OTR_BROWSERAPIKEY"));

	my $old_location  = _val($pcfg->param("LOCATION.location"));
	my $old_radius    = _val($pcfg->param("LOCATION.radius"));
	my $old_lat       = _val($pcfg->param("LOCATION.latitude"));
	my $old_lon       = _val($pcfg->param("LOCATION.longitude"));

	my $old_dyndns    = _val($pcfg->param("CONNECTION.dyndns"));
	my $old_port      = _val($pcfg->param("CONNECTION.port"));

	my @changes;
	push @changes, "RECORDER_MQTT.OTR_USER"           if $new_mqtt_user ne $old_mqtt_user;
	push @changes, "RECORDER_MQTT.OTR_PASS"           if $new_mqtt_pass ne $old_mqtt_pass;
	push @changes, "RECORDER_HTTP.OTR_BROWSERAPIKEY"  if $new_api       ne $old_api;

	push @changes, "LOCATION.location"               if $new_location  ne $old_location;
	push @changes, "LOCATION.radius"                 if $new_radius    ne $old_radius;
	push @changes, "LOCATION.latitude"               if $new_lat       ne $old_lat;
	push @changes, "LOCATION.longitude"              if $new_lon       ne $old_lon;

	push @changes, "CONNECTION.dyndns"               if $new_dyndns    ne $old_dyndns;
	push @changes, "CONNECTION.port"                 if $new_port      ne $old_port;

	if (@changes) {
		LOGDEB "Recorder config needs update, changed keys: " . join(", ", @changes);
		return 1;
	}
	return 0;
}

# Writes /etc/default/ot-recorder from current inputs
use File::Copy qw(copy move);

sub write_recorder_default_file
{
    my $mqtt_user = _val($mqttcred->{brokeruser});
    my $mqtt_pass = _val($mqttcred->{brokerpass});

    my $tmpfile   = $lbpdatadir . "/ot-recorder.txt";
    my $savefile  = $lbpconfigdir . "/ot-recorder";
    my $finalfile = "/etc/default/ot-recorder";

    my $fh;
    unless (open($fh, '>', $tmpfile)) {
        LOGCRIT "Unable to create $tmpfile: $!";
        return 0;
    }

    print $fh "OTR_STORAGEDIR=\"/var/spool/owntracks/recorder/store\"\n";
    print $fh "OTR_HOST=\"localhost\"\n";
    print $fh "OTR_PORT=\"1883\"\n";
    print $fh "OTR_USER=\"$mqtt_user\"\n";
    print $fh "OTR_PASS=\"$mqtt_pass\"\n";
    print $fh "OTR_HTTPHOST=\"$myip\"\n";
    print $fh "OTR_HTTPPORT=\"$recorderhttpport\"\n";
    print $fh "OTR_BROWSERAPIKEY=\"" . _val($R::googleapikey) . "\"\n";
    print $fh "OTR_TOPICS=\"owntracks/# owntracks/+/+\"\n";
    close $fh;

    move($tmpfile, $savefile) or do {
        LOGCRIT "move($tmpfile -> $savefile) failed: $!";
        return 0;
    };

    my $rc = system('sudo', '/bin/cp', '-f', $savefile, $finalfile);
    if ($rc != 0) {
        LOGCRIT "sudo cp to $finalfile failed (rc=$rc)";
        return 0;
    }

    LOGOK "Recorder config file saved to $finalfile";
    return 1;
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
	#$pcfg->delete("CONNECTION.migration");
	$pcfg->save() or &error;
	unlink glob $lbphtmlauthdir."/files/user_app/*.*";
	unlink glob $lbphtmlauthdir."/files/*.*";
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
    # OwnTracks Recorder
    $pids{'recorder'} = trim(
        `pgrep -x ot-recorder 2>/dev/null | head -n 1`
    );

    my $mqtt_pid = "";

    # MQTT Gateway V2:
    # Zuerst die offizielle PID-Datei verwenden.
    my $v2_pidfile = "/dev/shm/mqtt_gateway.pid";

    if (-r $v2_pidfile) {
        if (open my $fh, "<", $v2_pidfile) {
            my $pid = <$fh>;
            close $fh;

            $pid = trim($pid // "");

            if ($pid =~ /^\d+$/ && -d "/proc/$pid") {
                $mqtt_pid = $pid;
            }
        }
    }

    # V2-Fallback, falls die PID-Datei fehlt
    if (!$mqtt_pid) {
        $mqtt_pid = trim(
            `pgrep -f '[m]qtt_gateway\\.py' 2>/dev/null | head -n 1`
        );
    }

    # MQTT Gateway V1 als Fallback
    if (!$mqtt_pid) {
        $mqtt_pid = trim(
            `pgrep -x mqttgateway.pl 2>/dev/null | head -n 1`
        );
    }

    $pids{'mqttgateway'} = $mqtt_pid;

    # Mosquitto Broker
    $pids{'mosquitto'} = trim(
        `pgrep -x mosquitto 2>/dev/null | head -n 1`
    );
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
#!/usr/bin/perl -w

# ToDo
# tid in Abhängigkeit vom User - DONE
# Uninstall Script - DONE
# Pre-root anpassen
# MQTT Settings aus Perl raus aktualisieren - NO

##########################################################################
# Modules required
##########################################################################

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
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
our $mqtt_account;
our $mqtt_pass;

my $ip 							= LoxBerry::System::get_localip();
my $helptemplatefilename		= "help.html";
my $languagefile 				= "owntracks.ini";
my $maintemplatefilename	 	= "owntracks.html";
my $errortemplatefilename 		= "error.html";
my $pluginconfigfile 			= "owntracks.cfg";
my $recorderhttpport 			= "8083";
#my $file 						= "/etc/default/ot-recorder";
my $pluginlogfile				= "owntracks.log";
my $helplink 					= "https://www.loxwiki.eu/display/LOXBERRY/Owntracks";
#my $log 						= LoxBerry::Log->new ( name => 'Owntracks UI', filename => $lbplogdir ."/". $pluginlogfile, append => 1, addtime => 1 );
my $pcfg 						= new Config::Simple($lbpconfigdir . "/" . $pluginconfigfile);
our $error_message				= "";


##########################################################################
# Set new config options for upgrade installations
##########################################################################

#if (!defined $pcfg->param("CONNECTION.tls")) {
#	$pcfg->param("tls", "");
#} 

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

# read all POST-Parameter in namespace "R".
my $cgi = CGI->new;
$cgi->import_names('R');



#########################################################################
## Handle all ajax requests 
#########################################################################

my $q = $cgi->Vars;
my $saveformdata = $q->{saveformdata};

my %pids;
my $template;

if( $q->{ajax} ) 
{
	#require JSON;
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
	&form;
	exit;
}

my $log = LoxBerry::Log->new ( name => 'Owntracks UI', filename => $lbplogdir ."/". $pluginlogfile, append => 1, addtime => 1 );

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
# Check App Config file dir
##########################################################################

if (!-d $lbphtmlauthdir . "/files") 
{	
	mkdir $lbphtmlauthdir . "/files";
	mkdir $lbphtmlauthdir . "/files/user_app";
	mkdir $lbphtmlauthdir . "/files/user_photo";
	LOGOK "App config file and photo directory created";
} else {
	LOGDEB "App config file and photo directory already there";
}

##########################################################################
# Check if MQTT Plugin is installed
##########################################################################

my $mqtt = $lbhomedir . "/config/plugins/mqttgateway/mqtt.json";
if (!-r $mqtt) 
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
	my $credfile = "$lbhomedir/config/plugins/mqttgateway/cred.json";
	my $jsonobj = LoxBerry::JSON->new();
	my $mqttcfg = $jsonobj->open(filename => $credfile);

	$mqtt_account = $mqttcfg->{Credentials}{brokeruser};
	$mqtt_pass = $mqttcfg->{Credentials}{brokerpass};
	LOGDEB "MQTT credentials obtained";
	
	# get MQTT Config
	my $configfile = "$lbhomedir/config/plugins/mqttgateway/mqtt.json";
	my $jsonobj1 = LoxBerry::JSON->new();
	my $mqttpcfg = $jsonobj1->open(filename => $configfile);

	$mqtt_host = $mqttpcfg->{Main}{brokeraddress};
	LOGDEB "MQTT hostname obtained";
	
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

	if (-r $mqtt) 
	{
		$navbar{50}{Name} = "$SL{'BASIC.NAVBAR_SIXTH'}";
		$navbar{50}{URL} = 'http://'.$ip.":".lbwebserverport().'/admin/plugins/mqttgateway/index.cgi';
		$navbar{50}{target} = '_blank';
	}

	$navbar{90}{Name} = "$SL{'BASIC.NAVBAR_FIVETH'}";
	$navbar{90}{URL} = './index.cgi?do=logfiles';
	

if ($R::saveformdata) {
	&save;
}

if(!defined $do or $do eq "form") {
	$navbar{10}{active} = 1;
	$template->param("FORM", "1");
	&form;
} elsif ($do eq "tracking") {
	$navbar{40}{active} = 1;
	$template->param("TRACKING", "1");
	printtemplate();
} elsif ($do eq "command") {
	$navbar{30}{active} = 1;
	$template->param("COMMAND", "1");
	&topics_form;
	#printtemplate();
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
	
	my %userconfig = $pcfg->vars();	
	foreach my $key (keys %userconfig) {
		if ( $key =~ /^USER/ ) {
			$countuser++;
			my @fields = $pcfg->param($key);
			$rowsuser .= "<tr><td style='width: 4%;'><INPUT type='checkbox' style='width: 100%' name='chkuser$countuser' id='chkuser$countuser' align='left'/></td>\n";
			$rowsuser .= "<td style='width: 22%'><input id='username$countuser' name='username$countuser' type='text' class='uname' placeholder='$SL{'MENU.USER_LISTING'}' value='$fields[0]' align='left' data-validation-error-msg='$SL{'VALIDATION.USER_NAME'}' data-validation-rule='^([äöüÖÜßÄ A-Za-z0-9\ ]){1,20}' style='width: 100%;'></td>\n";
			$rowsuser .= "<td style='width: 4%'><input name='create$countuser' id='create$countuser' class='createconfbutton' type='button' data-role='button' data-inline='true' data-mini='true' onclick='' data-icon='check' value='$SL{'BUTTON.NEW_CONFIG'}'></td>\n";
			
			my $filecheck = "/var/spool/owntracks/recorder/store/last/loxberry/".lc($fields[0])."/loxberry-".lc($fields[0]).".json";
			my $filecreationcheck = "$lbphtmlauthdir/files/user_app/$fields[0].otrc";
						
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
		$rowsuser .= "<tr><td colspan=3>" . $SL{'VALIDATION.USER_EMPTY'} . "</td></tr>\n";
	}
	LOGDEB "$countuser User has been loaded.";
	$rowsuser .= "<input type='hidden' id='countuser' name='countuser' value='$countuser'>\n";
	$template->param("ROWSUSER", $rowsuser);
	
	# execute check if User(s) need to be migrated
	migrate_user($countuser);
	
	#$content = $filecheck;
	#print_test($content);
	#exit;
	
	printtemplate();
	exit;
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
	LOGINF "Start writing configuration file";
	
	my $trackstatus = $R::track;
	if ($trackstatus eq "true")  {
		compare_config();
		if ($count > 1)  {
			$pcfg->param("RECORDER_HTTP.OTR_BROWSERAPIKEY", "$R::googleapikey");
			$pcfg->param("RECORDER_MQTT.OTR_USER", "$mqtt_account");
			$pcfg->param("RECORDER_MQTT.OTR_HOST", "$mqtt_host");
			$pcfg->param("RECORDER_MQTT.OTR_PASS", "$mqtt_pass");
			$pcfg->param("CONNECTION.track", "true");
			$pcfg->save() or &error;
			recorder_config();
			LOGOK "Recorder settings saved, recorder restarted";
		}
	} else {
		$pcfg->param("CONNECTION.track", "false");
		system("sudo systemctl stop ot-recorder");
		LOGDEB "Recorder stopped";
	}
		
	$pcfg->param("CONNECTION.dyndns", "$R::dyndns");
	$pcfg->param("CONNECTION.port", "$R::port");
	# turn on if TLS works
	#$pcfg->param("CONNECTION.tls", "$R::tls");
	$pcfg->param("LOCATION.location", "$R::location");
	$pcfg->param("LOCATION.radius", "$R::radius");
	$pcfg->param("LOCATION.latitude", "$R::latitude");
	$pcfg->param("LOCATION.longitude", "$R::longitude");
	$pcfg->param("RECORDER_HTTP.OTR_HTTPHOST", "$myip");
	$pcfg->param("RECORDER_HTTP.OTR_HTTPPORT", "$recorderhttpport");
	
	# save all user
	for ($i = 1; $i <= $countuser; $i++) {
		my $username = quotemeta(param("username$i"));
		if ( param("chkuser$i") ) { # if radio should be deleted
			$pcfg->delete("USER$i.name", $username);
			$pcfg->delete("USER$i");
			LOGDEB "User: $username deleted";
		} else { # save
			$pcfg->param("USER$i.name", $username);
			LOGDEB "User: $username saved";
		}
	}
	$pcfg->save() or &error;
	LOGOK "All settings has been saved";
		
	# SAVE_MESSAGE
	$template->param("SAVE" => $SL{'BUTTON.SAVE_MESSAGE'});
	$template->param("FORM", "1");
	
	&form;
	#$content = $R::track;
	#print_test($content);
	#exit;
}


########################################################################
# Topics Form 
########################################################################
sub topics_form
{
	require "$lbhomedir/bin/plugins/mqttgateway/libs/LoxBerry/JSON/JSONIO.pm";
	require POSIX;
	
	my $datafile = "/dev/shm/mqttgateway_topics.json";
	my $relayjsonobj = LoxBerry::JSON::JSONIO->new();
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


##########################################################################
# Sub Update MQTT
##########################################################################

sub update_mqtt
{
	# get MQTT Config
	my $configfile = "$lbhomedir/config/plugins/mqttgateway/mqtt.json";
	my $jsonobj1 = LoxBerry::JSON->new();
	my $mqttpcfg = $jsonobj1->open(filename => $configfile);

	$mqtt_conv = $mqttpcfg->{Main}{conversions};
	$mqtt_subs = $mqttpcfg->{Main}{subscriptions};
	
}

#####################################################
# Sub compare_config
#####################################################

sub compare_config 
{	
	$count = 1;
	
	# compare config in order to check if recorder require updates
	$mqtt_account = $mqttcfg->{Credentials}{brokeruser};
	$mqtt_pass = $mqttcfg->{Credentials}{brokerpass};
	$mqtt_host = $mqttpcfg->{Main}{brokeraddress};
	my $saved_track = $pcfg->param("CONNECTION.track");
	my $saved_mqtt_user = $pcfg->param("RECORDER_MQTT.OTR_USER");
	my $saved_mqtt_pass = $pcfg->param("RECORDER_MQTT.OTR_PASS");
	my $saved_mqtt_host = $pcfg->param("RECORDER_MQTT.OTR_HOST");
	my $saved_mqtt_api = $pcfg->param("RECORDER_HTTP.OTR_BROWSERAPIKEY");
	
	if (($mqtt_account ne $saved_mqtt_user))  {
		$count++;
	}
	if ($mqtt_pass ne $saved_mqtt_pass)  {
		$count++;
	}
	if ($mqtt_host ne $saved_mqtt_host)  {
		$count++;
	}
	if ($R::googleapikey ne $saved_mqtt_api)  {
		$count++;
	}
	if ($R::track ne $saved_track)  {
		$count++;
	}
}


#####################################################
# Sub Recorder Configuration
#####################################################

sub recorder_config 
{
	my $file = $lbpdatadir."/ot-recorder.txt";

	# Use the open() function to create the file.
	unless(open FILE, '>'.$file) {
		# Die with error message 
		# if we can't open it.
		LOGCRIT "\nUnable to create $file\n";
	}

	# Write some text to the file.
	print FILE "OTR_STORAGEDIR=\"/var/spool/owntracks/recorder/store\"\n";
	print FILE "OTR_HOST=\"$mqtt_host\"\n";
	print FILE "OTR_PORT=\"1883\"\n";
	print FILE "OTR_USER=\"$mqtt_account\"\n";
	print FILE "OTR_PASS=\"$mqtt_pass\"\n";
	print FILE "OTR_HTTPHOST=\"$myip\"\n";
	print FILE "OTR_HTTPPORT=\"$recorderhttpport\"\n";
	#print FILE "OTR_HTTPLOGDIR=\n";
	print FILE "OTR_BROWSERAPIKEY=\"$R::googleapikey\"\n";
	print FILE "OTR_TOPICS=\"owntracks/# owntracks/+/+\"\n";

	# close the file.
	close FILE;
	
	# copy newly created file to destination
	my $savefile = $lbpconfigdir."/ot-recorder";
	my $finalfile = "/etc/default/ot-recorder";
	rename $file, $lbpconfigdir."/ot-recorder";
	copy $savefile, $finalfile;
	`cd $lbpbindir ; $lbpbindir/restart.sh > /dev/null 2>&1 &`;
	#system("/bin/sh $lbpbindir/restart.sh");
	unlink $lbpconfigdir."/ot-recorder";
	return;
}


######################################################################
# AJAX functions
######################################################################

sub pids 
{
	$pids{'recorder'} = (split(" ",`ps -A | grep \"ot-recorder\"`))[0];
	$pids{'mqttgateway'} = trim(`pgrep mqttgateway.pl`) ;
	$pids{'mosquitto'} = trim(`pgrep mosquitto`) ;
	LOGDEB "PIDs updated";
}	

sub ajax_header
{
	print $cgi->header(
			-type => 'application/json',
			-charset => 'utf-8',
			-status => '200 OK',
	);	
	LOGOK "AJAX posting received and processed";
}	




#####################################################
# Form-Tracking (old)
#####################################################

sub tracking 
{
	topics_form();
	printtemplate();
	exit;
}


#####################################################
# Sub migrate User accounts
#####################################################

sub migrate_user 
{	
	if ($pcfg->param("CONNECTION.migration") ne "completed")  {
		# Migrate
		for ($i = 1; $i <= $countuser; $i++) {
			our $old_user = $pcfg->param("USER.name" . "[$i]");
			$pcfg->param("USER$i.name", "$old_user");
			LOGDEB "Migration: USER.name$i=$old_user has been migrated to USER$i.name=$old_user";
		}
		# delete
		for ($i = 1; $i <= $countuser; $i++) {
			$pcfg->delete( "USER.name" . "[$i]" );
			$pcfg->delete( "USER" );
		}
		$pcfg->param("CONNECTION.migration", "completed");
		$pcfg->save() or &error;
		my $filemove = qx(/usr/bin/php $lbphtmldir/migration_app_files.php);
	}
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
	# Print Template
	print "Content-Type: text/html; charset=utf-8\n\n"; 
	print "*********************************************************************************************";
	print "<br>";
	print " *** Ausgabe zu Testzwecken";
	print "<br>";
	print "*********************************************************************************************";
	print "<br>";
	print "<br>";
	print $content;
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
			LOGEND "Finished successful";
		}
	}
}
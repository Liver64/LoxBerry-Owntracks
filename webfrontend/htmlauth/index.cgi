#!/usr/bin/perl -w

##########################################################################
# Modules required
##########################################################################

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;

use CGI;
use CGI qw( :standard);
use LWP::Simple;
use JSON qw( decode_json );
use utf8;
use warnings;
use strict;
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
my $helplink;
my $helptemplate;
our $content;
our $template;
our %navbar;

my $helptemplatefilename		= "help.html";
my $languagefile 				= "owntracks.ini";
my $maintemplatefilename	 	= "owntracks.html";
my $errortemplatefilename 		= "error.html";
my $pluginconfigfile 			= "owntracks.cfg";
my $pluginlogfile				= "owntracks.log";
my $log 						= LoxBerry::Log->new ( name => 'Owntracks UI', filename => $lbplogdir ."/". $pluginlogfile, append => 1, addtime => 1 );
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
	LOGDEB "The Owntracks config file has been loaded";
}

##########################################################################
# Check App Config file dir
##########################################################################

if (!-d $lbphtmlauthdir . "/files") 
{	
	mkdir $lbphtmlauthdir . "/files";
	LOGOK "App config file directory created";
} else {
	LOGDEB "App config file directory already there";
}

##########################################################################
# Check if MQTT Plugin is installed
##########################################################################

if (!-r $lbhomedir . "/config/plugins/mqttgateway/mqtt.json") 
{
	LOGCRIT "It seems that MQTT Plugin is not installed";
	$error_message = $ERR{'ERRORS.ERR_CHECK_MQTT_PLUGIN'};
	&error; 
}

##########################################################################
# Initiate Main Template
##########################################################################
inittemplate();


##########################################################################
# Some Settings
##########################################################################

$template->param("LBHOSTNAME", lbhostname());
$template->param("LBADR", lbhostname().":".lbwebserverport());
$template->param("LBLANG", $lblang);
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

$navbar{40}{Name} = "$SL{'BASIC.NAVBAR_FOURTH'}";
$navbar{40}{URL} = './index.cgi?do=tracking';

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
			$rowsuser .= "<td style='width: 90%'><div id='response$countuser'></div></td>\n";
		}
	}

	if ( $countuser < 1 ) {
		$rowsuser .= "<tr><td colspan=3>" . $SL{'VALIDATION.USER_EMPTY'} . "</td></tr>\n";
	}
	LOGDEB "$countuser User has been loaded.";
	$rowsuser .= "<input type='hidden' id='countuser' name='countuser' value='$countuser'>\n";
	$template->param("ROWSUSER", $rowsuser);
		
	#$content = "@{[%hash]}";
	#$content = $wcfg;
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
	
	$pcfg->param("CONNECTION.dyndns", "$R::dyndns");
	$pcfg->param("CONNECTION.port", "$R::port");
	#$pcfg->param("CONNECTION.tls", "$R::tls");
	$pcfg->param("LOCATION.location", "$R::location");
	$pcfg->param("LOCATION.radius", "$R::radius");
	$pcfg->param("LOCATION.latitude", "$R::latitude");
	$pcfg->param("LOCATION.longitude", "$R::longitude");
		
	# save all user
	for ($i = 1; $i <= $countuser; $i++) {
		if ( param("chkuser$i") ) { # if user should be deleted
			$pcfg->delete( "USER.name" . "[$i]" );
		} else { # save
			my $username = param("username$i");
			$pcfg->param( "USER.name" . "[$i]", "$username");
		}
	}
	$pcfg->save() or &error;
	LOGDEB "User has been saved.";
	LOGOK "All settings has been saved";
	
	#$content = $server_endpoint;
	#print_test($content);
	#exit;
	
	# SAVE_MESSAGE
	$template->param("SAVE" => $SL{'BUTTON.SAVE_MESSAGE'});
	$template->param("FORM", "1");
	&form;
	exit;
}


########################################################################
# Topics Form 
########################################################################
sub topics_form
{
	require "$lbhomedir/bin/plugins/mqttgateway/libs/LoxBerry/JSON/JSONIO.pm";
	require POSIX;
	
	my $datafile = "/dev/shm/mqttgateway_topic.json";
	#my $datafile = "/dev/shm/mqttgateway_topics.json";
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

#####################################################
# Form-Sub
#####################################################

sub tracking 
{
	topics_form();
	printtemplate();
	exit;
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
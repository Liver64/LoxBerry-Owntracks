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

#my $namef;
#my $value;
#my %query;
my $template_title;
my $error;
my $saveformdata = 0;
my $do = "form";
my $helplink;
my $helptemplate;
our $content;
our $template;
our %navbar;
#our %weatherconfig;

my $helptemplatefilename		= "help.html";
my $languagefile 				= "owntracks.ini";
my $maintemplatefilename	 	= "mqtt_output.html";
my $pluginconfigfile 			= "owntracks.cfg";
my $pluginlogfile				= "owntracks.log";
my $lbip 						= LoxBerry::System::get_localip();
my $lbport						= lbwebserverport();
my $log 						= LoxBerry::Log->new ( name => 'Owntracks UI', filename => $lbplogdir ."/". $pluginlogfile, append => 1, addtime => 1 );
my $pcfg 						= new Config::Simple($lbpconfigdir . "/" . $pluginconfigfile);
our $error_message				= "";

##########################################################################
# Read Settings
##########################################################################

# read language
my $lblang = lblanguage();

# Read Plugin Version
my $sversion = LoxBerry::System::pluginversion();

# Read LoxBerry Version
my $lbversion = LoxBerry::System::lbversion();

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
# Init Main Template
##########################################################################
inittemplate();

##########################################################################
# Set LoxBerry SDK to debug in plugin 
##########################################################################

if($log->loglevel() eq "7") {
	$LoxBerry::System::DEBUG 	= 1;
	$LoxBerry::Web::DEBUG 		= 1;
	$LoxBerry::Log::DEBUG		= 1;
}


##########################################################################
# Language Settings
##########################################################################

$template->param("LBHOSTNAME", lbhostname());
$template->param("LBLANG", $lblang);

#LOGDEB "Read main settings from " . $languagefile . " for language: " . $lblang;

#************************************************************************

# übergibt Plugin Verzeichnis an HTML
$template->param("PLUGINDIR" => $lbpplugindir);

##########################################################################
# Main program
##########################################################################

$navbar{10}{Name} = "$SL{'BASIC.NAVBAR_FIRST'}";
$navbar{10}{URL} = './index.cgi';

if ($pcfg->param("LOCATION.longitude") eq '' or $pcfg->param("LOCATION.latitude") eq '')  
{
	$navbar{20}{Name} = "$SL{'BASIC.NAVBAR_SECOND'}";
	$navbar{20}{URL} = 'https://www.google.com/maps';
	$navbar{20}{target} = '_blank';
}

$navbar{30}{Name} = "$SL{'BASIC.NAVBAR_THIRD'}";
$navbar{30}{URL} = './mqtt_output.cgi';

$navbar{40}{Name} = "$SL{'BASIC.NAVBAR_FOURTH'}";
$navbar{40}{URL} = './tracking.cgi';

$navbar{90}{Name} = "$SL{'BASIC.NAVBAR_FIVETH'}";
$navbar{90}{URL} = './index.cgi?do=logfiles';

if ($R::saveformdata) {
	&save;
}

if(!defined $do or $do eq "form") {
	$navbar{1}{active} = 1;
	$template->param("FORM", "1");
	&form;
} elsif ($do eq "logfiles") {
	LOGTITLE "Show logfiles";
	$navbar{99}{active} = 1;
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
	topics_form();
	printtemplate();
	exit;
}


########################################################################
# Topics Form 
########################################################################
sub topics_form
{
	require "$lbhomedir/bin/plugins/mqttgateway/libs/LoxBerry/JSON/JSONIO.pm";
	require POSIX;
	
	#my $datafile = "/dev/shm/mqttgateway_topic.json";
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
	$http_table .= qq { <table class="topics_table_http" id="http_table" name="http_table" data-filter="true"> };
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
	$udp_table .= qq { <table class="topics_table_udp" id="udp_table" name="udp_table" data-filter="true"> };
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
	
	if (my $log) {
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
<?php
header('Content-Type: text/html; charset=utf-8');
require_once "loxberry_system.php";

$srcDir = LBPHTMLAUTHDIR."/files/user_app/";
$destDir = LBPDATADIR."/user_config_files/";
echo '<PRE>';

if (file_exists($destDir)) {
  if (is_dir($destDir)) {
    if (is_writable($destDir)) {
      if ($handle = opendir($srcDir)) {
        while (false !== ($file = readdir($handle))) {
          if (is_file($srcDir . '/' . $file)) {
            rename($srcDir . '/' . $file, $destDir . '/' . $file);
          }
        }
        closedir($handle);
      } else {
        echo "$srcDir could not be opened.\n";
      }
    } else {
      echo "$destDir is not writable!\n";
    }
  } else {
    echo "$destDir is not a directory!\n";
  }
} else {
  echo "$destDir does not exist\n";
}
rmdir( LBPHTMLAUTHDIR."/files/user_app/");
rmdir( LBPHTMLAUTHDIR."/files/");
?>
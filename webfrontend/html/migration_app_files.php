<?php
header('Content-Type: text/html; charset=utf-8');
require_once "loxberry_system.php";

$src = LBPHTMLAUTHDIR."/files/";
$dest = LBPHTMLAUTHDIR."/files/user_app/";

$files = scandir($src);
foreach($files as $file){
    if (is_file($src.$file)) {
        $rename_file = $dest.$file;
		rename($src.$file, $rename_file);
    }
}
$files_ren = scandir($dest);
foreach($files_ren as $file1){
    if (is_file($dest.$file1)) {
		$teile = explode("_", $file1);
		copy($dest.$file1, $dest.$teile[1].".otrc");
    }
}

?>
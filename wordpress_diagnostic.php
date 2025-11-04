<?php
/**
 * WordPress Environment Diagnostic Script
 *
 * Place this file in your WordPress root directory and access it via browser
 * e.g., http://yoursite.com/wordpress_diagnostic.php
 *
 * This will help diagnose why themes are crashing WordPress
 */

// Security check - delete this file after use
$diagnostic_key = 'wpgen-diagnostic';

?>
<!DOCTYPE html>
<html>
<head>
    <title>WordPress Environment Diagnostic</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #0073aa; border-bottom: 2px solid #0073aa; padding-bottom: 10px; }
        h2 { color: #23282d; margin-top: 30px; }
        .section { margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #0073aa; }
        .good { color: #46b450; font-weight: bold; }
        .warning { color: #f0b849; font-weight: bold; }
        .error { color: #dc3232; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        td, th { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f1f1f1; font-weight: bold; }
        .code { background: #282c34; color: #abb2bf; padding: 15px; border-radius: 4px; overflow-x: auto; font-family: monospace; }
        .alert { padding: 15px; margin: 20px 0; border-radius: 4px; }
        .alert-error { background: #fdeaea; border-left: 4px solid #dc3232; }
        .alert-warning { background: #fef8e7; border-left: 4px solid #f0b849; }
        .alert-success { background: #ecf7ed; border-left: 4px solid #46b450; }
    </style>
</head>
<body>
<div class="container">
    <h1>WordPress Environment Diagnostic Report</h1>
    <p>Generated: <?php echo date('Y-m-d H:i:s'); ?></p>

    <?php
    $errors = [];
    $warnings = [];
    $success = [];

    // Check if WordPress is loaded
    $wp_config_path = __DIR__ . '/wp-config.php';
    $wp_load_path = __DIR__ . '/wp-load.php';

    echo '<div class="section">';
    echo '<h2>1. WordPress Installation Check</h2>';

    if (file_exists($wp_config_path)) {
        echo '<p class="good">✓ wp-config.php found</p>';
        $success[] = 'WordPress configuration file exists';
    } else {
        echo '<p class="error">✗ wp-config.php NOT FOUND</p>';
        $errors[] = 'WordPress configuration file missing - this is not a valid WordPress installation';
    }

    if (file_exists($wp_load_path)) {
        echo '<p class="good">✓ wp-load.php found</p>';
        $success[] = 'WordPress loader file exists';
    } else {
        echo '<p class="error">✗ wp-load.php NOT FOUND</p>';
        $errors[] = 'WordPress loader missing - this is not a valid WordPress installation';
    }

    echo '</div>';

    // PHP Environment
    echo '<div class="section">';
    echo '<h2>2. PHP Environment</h2>';
    echo '<table>';
    echo '<tr><th>Setting</th><th>Value</th><th>Status</th></tr>';

    $php_version = phpversion();
    $php_ok = version_compare($php_version, '7.4', '>=');
    echo '<tr><td>PHP Version</td><td>' . $php_version . '</td><td>';
    if ($php_ok) {
        echo '<span class="good">✓ OK</span>';
        $success[] = "PHP version {$php_version} is compatible";
    } else {
        echo '<span class="error">✗ TOO OLD (need 7.4+)</span>';
        $errors[] = "PHP version {$php_version} is too old - WordPress requires 7.4 or higher";
    }
    echo '</td></tr>';

    $memory_limit = ini_get('memory_limit');
    echo '<tr><td>Memory Limit</td><td>' . $memory_limit . '</td><td>';
    $memory_bytes = wp_convert_hr_to_bytes($memory_limit);
    if ($memory_bytes >= 268435456) { // 256MB
        echo '<span class="good">✓ OK</span>';
    } elseif ($memory_bytes >= 134217728) { // 128MB
        echo '<span class="warning">⚠ Low (recommend 256MB+)</span>';
        $warnings[] = "Memory limit is {$memory_limit} - recommend 256MB or higher";
    } else {
        echo '<span class="error">✗ TOO LOW (need 128MB+)</span>';
        $errors[] = "Memory limit {$memory_limit} is too low - increase to 256MB";
    }
    echo '</td></tr>';

    $max_execution = ini_get('max_execution_time');
    echo '<tr><td>Max Execution Time</td><td>' . $max_execution . 's</td><td>';
    if ($max_execution == 0 || $max_execution >= 300) {
        echo '<span class="good">✓ OK</span>';
    } elseif ($max_execution >= 60) {
        echo '<span class="warning">⚠ Could be higher</span>';
    } else {
        echo '<span class="warning">⚠ Low</span>';
        $warnings[] = "Max execution time is {$max_execution}s - may cause timeouts";
    }
    echo '</td></tr>';

    $display_errors = ini_get('display_errors');
    echo '<tr><td>Display Errors</td><td>' . ($display_errors ? 'On' : 'Off') . '</td><td>';
    if ($display_errors) {
        echo '<span class="warning">⚠ Should be Off in production</span>';
    } else {
        echo '<span class="good">✓ OK</span>';
    }
    echo '</td></tr>';

    echo '</table>';
    echo '</div>';

    // Required PHP Extensions
    echo '<div class="section">';
    echo '<h2>3. Required PHP Extensions</h2>';
    echo '<table>';
    echo '<tr><th>Extension</th><th>Status</th></tr>';

    $required_extensions = [
        'mysqli' => 'Database connectivity',
        'json' => 'JSON parsing',
        'mbstring' => 'Multibyte string handling',
        'zip' => 'Plugin/theme installation',
        'gd' => 'Image processing',
        'curl' => 'HTTP requests',
        'xml' => 'XML parsing',
        'dom' => 'DOM manipulation',
    ];

    foreach ($required_extensions as $ext => $purpose) {
        $loaded = extension_loaded($ext);
        echo '<tr><td>' . $ext . ' <small>(' . $purpose . ')</small></td><td>';
        if ($loaded) {
            echo '<span class="good">✓ Loaded</span>';
        } else {
            echo '<span class="error">✗ Missing</span>';
            $errors[] = "PHP extension '{$ext}' is not loaded - required for {$purpose}";
        }
        echo '</td></tr>';
    }

    echo '</table>';
    echo '</div>';

    // Try to load WordPress
    if (file_exists($wp_load_path)) {
        echo '<div class="section">';
        echo '<h2>4. WordPress Core Load Test</h2>';

        try {
            // Suppress errors temporarily
            $old_error_reporting = error_reporting(0);

            // Try to load WordPress
            require_once($wp_load_path);

            error_reporting($old_error_reporting);

            if (function_exists('wp_version')) {
                global $wp_version;
                echo '<p class="good">✓ WordPress loaded successfully</p>';
                echo '<p><strong>WordPress Version:</strong> ' . $wp_version . '</p>';
                $success[] = "WordPress {$wp_version} loaded successfully";

                // Check if database is connected
                global $wpdb;
                if ($wpdb) {
                    $db_test = $wpdb->get_var("SELECT 1");
                    if ($db_test == 1) {
                        echo '<p class="good">✓ Database connection working</p>';
                        $success[] = 'Database connection is working';
                    } else {
                        echo '<p class="error">✗ Database connection failed</p>';
                        $errors[] = 'Database connection is not working';
                    }
                }

                // Check active theme
                $current_theme = wp_get_theme();
                if ($current_theme->exists()) {
                    echo '<p><strong>Active Theme:</strong> ' . $current_theme->get('Name') . ' (' . $current_theme->get('Version') . ')</p>';
                    echo '<p><strong>Theme Path:</strong> ' . $current_theme->get_stylesheet_directory() . '</p>';

                    // Check for common theme files
                    $theme_dir = $current_theme->get_stylesheet_directory();
                    $required_files = ['style.css', 'index.php'];
                    $optional_files = ['functions.php', 'header.php', 'footer.php', 'sidebar.php'];

                    echo '<p><strong>Theme Files:</strong></p><ul>';
                    foreach ($required_files as $file) {
                        $exists = file_exists($theme_dir . '/' . $file);
                        echo '<li>' . $file . ': ';
                        if ($exists) {
                            echo '<span class="good">✓ Found</span>';
                        } else {
                            echo '<span class="error">✗ Missing</span>';
                            $errors[] = "Required theme file '{$file}' is missing from active theme";
                        }
                        echo '</li>';
                    }
                    foreach ($optional_files as $file) {
                        $exists = file_exists($theme_dir . '/' . $file);
                        echo '<li>' . $file . ': ';
                        echo $exists ? '<span class="good">✓ Found</span>' : '<span>- Not found</span>';
                        echo '</li>';
                    }
                    echo '</ul>';
                }

            } else {
                echo '<p class="error">✗ WordPress loaded but wp_version() function not available</p>';
                $errors[] = 'WordPress loaded incompletely - core functions missing';
            }
        } catch (Exception $e) {
            echo '<p class="error">✗ Failed to load WordPress</p>';
            echo '<p><strong>Error:</strong> ' . htmlspecialchars($e->getMessage()) . '</p>';
            $errors[] = 'Failed to load WordPress: ' . $e->getMessage();
        }

        echo '</div>';
    }

    // Check error log
    echo '<div class="section">';
    echo '<h2>5. WordPress Debug Log</h2>';

    $debug_log = WP_CONTENT_DIR . '/debug.log';
    if (defined('WP_CONTENT_DIR') && file_exists($debug_log)) {
        $log_size = filesize($debug_log);
        echo '<p class="warning">⚠ Debug log exists (size: ' . size_format($log_size) . ')</p>';

        if ($log_size > 0) {
            $recent_log = file_get_contents($debug_log);
            $recent_lines = array_slice(explode("\n", $recent_log), -50);
            echo '<p><strong>Last 50 lines:</strong></p>';
            echo '<div class="code">' . htmlspecialchars(implode("\n", $recent_lines)) . '</div>';

            $warnings[] = 'WordPress debug log contains errors - check wp-content/debug.log';
        }
    } else {
        echo '<p>No debug log found. To enable error logging, add this to wp-config.php:</p>';
        echo '<div class="code">define(\'WP_DEBUG\', true);<br>define(\'WP_DEBUG_LOG\', true);<br>define(\'WP_DEBUG_DISPLAY\', false);<br>@ini_set(\'display_errors\', 0);</div>';
    }

    echo '</div>';

    // Summary
    echo '<div class="section">';
    echo '<h2>Summary</h2>';

    if (count($errors) > 0) {
        echo '<div class="alert alert-error">';
        echo '<h3>Critical Issues (' . count($errors) . ')</h3><ul>';
        foreach ($errors as $error) {
            echo '<li>' . htmlspecialchars($error) . '</li>';
        }
        echo '</ul></div>';
    }

    if (count($warnings) > 0) {
        echo '<div class="alert alert-warning">';
        echo '<h3>Warnings (' . count($warnings) . ')</h3><ul>';
        foreach ($warnings as $warning) {
            echo '<li>' . htmlspecialchars($warning) . '</li>';
        }
        echo '</ul></div>';
    }

    if (count($errors) == 0 && count($warnings) == 0) {
        echo '<div class="alert alert-success">';
        echo '<h3>✓ All checks passed</h3>';
        echo '<p>Your WordPress environment appears healthy. If themes are still crashing, the issue may be theme-specific.</p>';
        echo '</div>';
    }

    echo '</div>';

    // Helper function
    function wp_convert_hr_to_bytes($value) {
        $value = strtolower(trim($value));
        $bytes = (int) $value;

        if (strpos($value, 'g') !== false) {
            $bytes *= 1024 * 1024 * 1024;
        } elseif (strpos($value, 'm') !== false) {
            $bytes *= 1024 * 1024;
        } elseif (strpos($value, 'k') !== false) {
            $bytes *= 1024;
        }

        return $bytes;
    }

    function size_format($bytes) {
        if ($bytes >= 1073741824) {
            return number_format($bytes / 1073741824, 2) . ' GB';
        } elseif ($bytes >= 1048576) {
            return number_format($bytes / 1048576, 2) . ' MB';
        } elseif ($bytes >= 1024) {
            return number_format($bytes / 1024, 2) . ' KB';
        } else {
            return $bytes . ' bytes';
        }
    }
    ?>

    <div class="section">
        <h2>Next Steps</h2>
        <ol>
            <li>If critical issues are shown above, fix them before proceeding</li>
            <li>Enable WordPress debug logging (see section 5 above)</li>
            <li>Try activating your theme again</li>
            <li>Check wp-content/debug.log for the actual error message</li>
            <li>Share the debug.log error with the developer</li>
        </ol>
        <p><strong>⚠ IMPORTANT:</strong> Delete this diagnostic file after use for security reasons!</p>
    </div>
</div>
</body>
</html>

<?php
/**
 * Theme Directory PHP Test
 *
 * Place this file in your theme directory and access it directly:
 * http://yoursite.com/wp-content/themes/your-theme-name/theme_test.php
 *
 * This tests if PHP can execute in your theme directory at all.
 */
?>
<!DOCTYPE html>
<html>
<head>
    <title>Theme Directory PHP Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .good { color: green; font-weight: bold; }
        .error { color: red; font-weight: bold; }
        pre { background: #f4f4f4; padding: 15px; border-left: 4px solid #0073aa; }
    </style>
</head>
<body>
    <h1>Theme Directory PHP Test</h1>

    <?php if (function_exists('phpinfo')): ?>
        <p class="good">✓ PHP is executing in this directory</p>
    <?php else: ?>
        <p class="error">✗ PHP is NOT executing properly</p>
    <?php endif; ?>

    <h2>PHP Information</h2>
    <pre>
PHP Version: <?php echo phpversion(); ?>

Current Directory: <?php echo __DIR__; ?>

File: <?php echo __FILE__; ?>

Server Software: <?php echo $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown'; ?>

Document Root: <?php echo $_SERVER['DOCUMENT_ROOT'] ?? 'Unknown'; ?>
    </pre>

    <h2>Test Results</h2>
    <ul>
        <li>PHP Execution: <span class="good">✓ Working</span></li>
        <li>File Access: <span class="good">✓ This file is readable</span></li>
        <li>Theme Directory: <?php echo __DIR__; ?></li>
    </ul>

    <h2>Check These Theme Files</h2>
    <ul>
        <?php
        $theme_files = ['style.css', 'index.php', 'functions.php', 'header.php', 'footer.php'];
        foreach ($theme_files as $file) {
            $path = __DIR__ . '/' . $file;
            $exists = file_exists($path);
            $readable = $exists && is_readable($path);

            echo '<li>' . $file . ': ';
            if ($exists && $readable) {
                echo '<span class="good">✓ Found & Readable</span>';

                // For PHP files, try to check for syntax errors
                if (substr($file, -4) === '.php') {
                    $output = [];
                    $return_var = 0;
                    exec("php -l " . escapeshellarg($path) . " 2>&1", $output, $return_var);
                    if ($return_var === 0) {
                        echo ' <span class="good">(Syntax OK)</span>';
                    } else {
                        echo ' <span class="error">(Syntax Error: ' . implode(' ', $output) . ')</span>';
                    }
                }
            } elseif ($exists) {
                echo '<span class="error">✗ Found but NOT Readable</span>';
            } else {
                echo '<span>- Not found</span>';
            }
            echo '</li>';
        }
        ?>
    </ul>

    <h2>Test Loading functions.php</h2>
    <?php
    $functions_file = __DIR__ . '/functions.php';
    if (file_exists($functions_file)) {
        echo '<p>Attempting to include functions.php...</p>';
        echo '<pre>';

        // Capture any output or errors
        ob_start();
        $error_before = error_get_last();

        try {
            include_once($functions_file);
            $output = ob_get_clean();

            $error_after = error_get_last();

            if ($error_after && $error_after !== $error_before) {
                echo '<span class="error">✗ Error occurred:</span>' . "\n";
                echo htmlspecialchars(print_r($error_after, true));
            } else {
                echo '<span class="good">✓ functions.php loaded successfully</span>' . "\n";
                if ($output) {
                    echo "Output:\n" . htmlspecialchars($output);
                }
            }
        } catch (Exception $e) {
            ob_end_clean();
            echo '<span class="error">✗ Exception:</span> ' . htmlspecialchars($e->getMessage()) . "\n";
            echo htmlspecialchars($e->getTraceAsString());
        } catch (Error $e) {
            ob_end_clean();
            echo '<span class="error">✗ Fatal Error:</span> ' . htmlspecialchars($e->getMessage()) . "\n";
            echo htmlspecialchars($e->getTraceAsString());
        }

        echo '</pre>';
    } else {
        echo '<p>functions.php not found in this directory</p>';
    }
    ?>

    <p><strong>Delete this file after testing!</strong></p>
</body>
</html>

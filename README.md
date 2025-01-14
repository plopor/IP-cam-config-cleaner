# IP-cam-config-cleaner
Python script for deduplicating and validating IP cam links for viewer XML configuration files.
If validate-urls is t, uses concurrent head requests to filter dead urls. Will generate a deduplicated list of IP cams.

Usage:
python modifyConfigs.py path/to/config.xml validate-urls(t/f)

#config: global configuration options

# with slash at end !!
database="sqlite:///db.sqlite"

# Maximum size of a proposal upload
# As we all know, Bitcoin Unlimited loves 1MB!
max_upload=1024*1024

# Test mode with test keys etc.
# Disable for release!!
test_mode = True 

# Dangerous: Puts flask into debug mode!
# Disable for release!!
debug_mode=True

# Use test prefix for voting?
use_test_prefix = True

# Prefix for action strings
# A separate test prefix is chosen so that it is clear to everyone
# that votes done using this test prefix are not meant to have any
# relevance.
test_action_prefix="bitcoin-unlimited-voting-test-data-without-relevance: "
normal_action_prefix="bitcoin-unlimited-voting: "

action_prefix = test_action_prefix if use_test_prefix else normal_action_prefix

# Web root as seen from the outside
# Used to build path strings for HTML templates
web_root="/voting/" 

# Internal prefix for web stuff
web_prefix_internal = "/api1/"

# Timeout for members (in seconds) - if they didn't vote for this long
# on anything, they are expired
member_expiry_time = 86400 * 365

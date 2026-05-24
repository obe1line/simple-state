# CMake generated Testfile for 
# Source directory: /home/csz/Code/simple-state
# Build directory: /home/csz/Code/simple-state
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[state_machine_tests]=] "/home/csz/Code/simple-state/state_machine_tests")
set_tests_properties([=[state_machine_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;20;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")
add_test([=[mermaid_generate_blinky_header]=] "/usr/bin/python3.13" "/home/csz/Code/simple-state/tools/mermaid_to_controller.py" "--input" "/home/csz/Code/simple-state/diagrams/blinky.mmd" "--output" "/home/csz/Code/simple-state/generated/blinky_controller_generated.hpp" "--user-output" "/home/csz/Code/simple-state/generated/blinky_controller_user.hpp" "--overwrite-user-output")
set_tests_properties([=[mermaid_generate_blinky_header]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;35;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")
add_test([=[mermaid_generate_uart_header]=] "/usr/bin/python3.13" "/home/csz/Code/simple-state/tools/mermaid_to_controller.py" "--input" "/home/csz/Code/simple-state/diagrams/uart.mmd" "--output" "/home/csz/Code/simple-state/generated/uart_controller_generated.hpp" "--user-output" "/home/csz/Code/simple-state/generated/uart_controller_user.hpp" "--overwrite-user-output")
set_tests_properties([=[mermaid_generate_uart_header]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;35;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")
add_test([=[mermaid_compare_blinky_transitions]=] "/usr/bin/python3.13" "/home/csz/Code/simple-state/tools/compare_state_transitions.py" "--expected-generated" "/home/csz/Code/simple-state/include/simple_state/generated/blinky_controller_generated.hpp" "--expected-user" "/home/csz/Code/simple-state/include/simple_state/blinky_controller_user.hpp" "--actual-generated" "/home/csz/Code/simple-state/generated/blinky_controller_generated.hpp" "--actual-user" "/home/csz/Code/simple-state/generated/blinky_controller_user.hpp")
set_tests_properties([=[mermaid_compare_blinky_transitions]=] PROPERTIES  DEPENDS "mermaid_generate_blinky_header" _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;46;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")

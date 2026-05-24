# CMake generated Testfile for 
# Source directory: /home/csz/Code/simple-state
# Build directory: /home/csz/Code/simple-state
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[state_machine_tests]=] "/home/csz/Code/simple-state/state_machine_tests")
set_tests_properties([=[state_machine_tests]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;20;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")
add_test([=[mermaid_generate_blinky_header]=] "/usr/bin/python3.13" "/home/csz/Code/simple-state/tools/mermaid_to_controller.py" "--input" "/home/csz/Code/simple-state/diagrams/blinky.mmd" "--output" "/home/csz/Code/simple-state/generated/blinky_from_mermaid.hpp" "--controller" "BlinkyController")
set_tests_properties([=[mermaid_generate_blinky_header]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;24;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")
add_test([=[mermaid_compare_blinky_transitions]=] "/usr/bin/python3.13" "/home/csz/Code/simple-state/tools/compare_state_transitions.py" "--expected" "/home/csz/Code/simple-state/include/simple_state/blinky_controller.hpp" "--actual" "/home/csz/Code/simple-state/generated/blinky_from_mermaid.hpp")
set_tests_properties([=[mermaid_compare_blinky_transitions]=] PROPERTIES  DEPENDS "mermaid_generate_blinky_header" _BACKTRACE_TRIPLES "/home/csz/Code/simple-state/CMakeLists.txt;33;add_test;/home/csz/Code/simple-state/CMakeLists.txt;0;")

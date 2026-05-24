cmake_minimum_required(VERSION 3.20)
project(simple_state LANGUAGES CXX)

find_package(Python3 COMPONENTS Interpreter REQUIRED)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(simple_state INTERFACE)
target_include_directories(simple_state INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_executable(stm32_state_demo src/demo_main.cpp)
target_link_libraries(stm32_state_demo PRIVATE simple_state)

add_executable(state_machine_tests tests/state_machine_test.cpp)
target_link_libraries(state_machine_tests PRIVATE simple_state)

enable_testing()
add_test(NAME state_machine_tests COMMAND state_machine_tests)

set(MERMAID_GENERATED_HEADER ${CMAKE_CURRENT_BINARY_DIR}/generated/blinky_from_mermaid.hpp)
set(MERMAID_GENERATED_USER_HEADER ${CMAKE_CURRENT_BINARY_DIR}/generated/blinky_from_mermaid_user.hpp)

add_test(
	NAME mermaid_generate_blinky_header
	COMMAND ${Python3_EXECUTABLE}
		${CMAKE_CURRENT_SOURCE_DIR}/tools/mermaid_to_controller.py
		--input ${CMAKE_CURRENT_SOURCE_DIR}/diagrams/blinky.mmd
		--output ${MERMAID_GENERATED_HEADER}
		--user-output ${MERMAID_GENERATED_USER_HEADER}
		--overwrite-user-output
		--controller BlinkyController
)

add_test(
	NAME mermaid_compare_blinky_transitions
	COMMAND ${Python3_EXECUTABLE}
		${CMAKE_CURRENT_SOURCE_DIR}/tools/compare_state_transitions.py
		--expected-generated ${CMAKE_CURRENT_SOURCE_DIR}/include/simple_state/generated/blinky_controller_generated.hpp
		--expected-user ${CMAKE_CURRENT_SOURCE_DIR}/include/simple_state/blinky_controller_user.hpp
		--actual-generated ${MERMAID_GENERATED_HEADER}
		--actual-user ${MERMAID_GENERATED_USER_HEADER}
)

set_tests_properties(
	mermaid_compare_blinky_transitions
	PROPERTIES DEPENDS mermaid_generate_blinky_header
)

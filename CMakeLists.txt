cmake_minimum_required(VERSION 3.20)
project(simple_state LANGUAGES CXX)

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

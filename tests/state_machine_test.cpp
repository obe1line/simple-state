#include <cassert>
#include <cstdint>
#include <iostream>
#include <string_view>

#include "simple_state/blinky_controller.hpp"
#include "simple_state/simulated_board.hpp"

namespace {

using Controller = simple_state::BlinkyController<simple_state::SimulatedBoard>;

void test_nominal_blink_path() {
    simple_state::SimulatedBoard board;
    Controller controller{board};

    controller.start();
    assert(std::string_view{controller.state_name()} == "Boot");
    assert(!controller.led_is_on());

    board.set_time(100);
    controller.run_once();
    assert(std::string_view{controller.state_name()} == "Idle");

    board.set_time(1100);
    controller.run_once();
    assert(std::string_view{controller.state_name()} == "LedOn");
    assert(controller.led_is_on());

    board.set_time(1350);
    controller.run_once();
    assert(std::string_view{controller.state_name()} == "LedOff");
    assert(!controller.led_is_on());

    board.set_time(2100);
    controller.run_once();
    assert(std::string_view{controller.state_name()} == "LedOn");
    assert(controller.led_is_on());
}

void test_fault_path() {
    simple_state::SimulatedBoard board;
    board.set_self_test_ok(false);
    Controller controller{board};

    controller.start();

    board.set_time(100);
    controller.run_once();
    assert(std::string_view{controller.state_name()} == "Fault");
    assert(controller.led_is_on());

    board.set_time(200);
    controller.run_once();
    assert(!controller.led_is_on());

    board.set_time(300);
    controller.run_once();
    assert(controller.led_is_on());
}

}  // namespace

int main() {
    test_nominal_blink_path();
    test_fault_path();
    std::cout << "All state machine tests passed.\n";
    return 0;
}

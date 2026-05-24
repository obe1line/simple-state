#include <cstdint>
#include <iostream>
#include <string_view>

#include "simple_state/blinky_controller.hpp"
#include "simple_state/simulated_board.hpp"

int main() {
    simple_state::SimulatedBoard board;
    simple_state::BlinkyController<simple_state::SimulatedBoard> controller{board};

    controller.start();

    const char* last_state = controller.state_name();
    std::cout << "t=0ms state=" << last_state << " led=" << controller.led_is_on() << '\n';

    for (std::uint32_t now_ms = 0; now_ms <= 2000; now_ms += 50) {
        board.set_time(now_ms);
        board.set_button_pressed(now_ms >= 300 && now_ms < 350);
        board.set_fault(now_ms >= 1450);

        controller.run_once();

        if (std::string_view{controller.state_name()} != last_state) {
            last_state = controller.state_name();
            std::cout << "t=" << now_ms << "ms state=" << last_state << " led=" << controller.led_is_on() << '\n';
        }
    }

    std::cout << "samples=" << board.led_history().size() << '\n';
    return 0;
}

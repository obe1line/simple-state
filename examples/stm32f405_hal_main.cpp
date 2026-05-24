#include <cstdint>

#include "simple_state/blinky_controller.hpp"
#include "simple_state/stm32f405_hal_board.hpp"
#include "stm32f4xx_hal.h"

namespace {

simple_state::Stm32f405RuntimeFlags g_runtime_flags{};

void SystemClock_Config();
void MX_GPIO_Init();
bool run_power_on_self_test();

using Board = simple_state::Stm32f405HalBoard;
using Controller = simple_state::BlinkyController<Board>;

}  // namespace

int main() {
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();

    g_runtime_flags.self_test_passed = run_power_on_self_test();
    g_runtime_flags.fault_active = false;

    const simple_state::Stm32f405HalBoardConfig board_config{
        .led_port = GPIOD,
        .led_pin = GPIO_PIN_12,
        .led_active_state = GPIO_PIN_SET,
        .button_port = GPIOA,
        .button_pin = GPIO_PIN_0,
        .button_pressed_state = GPIO_PIN_SET,
        .flags = &g_runtime_flags,
        .tick_reader = HAL_GetTick,
    };

    Board board{board_config};
    Controller controller{board};
    controller.start();

    while (true) {
        controller.run_once();

        if (__HAL_RCC_GET_FLAG(RCC_FLAG_IWDGRST) != RESET) {
            g_runtime_flags.fault_active = true;
        }
    }
}

extern "C" void SysTick_Handler(void) {
    HAL_IncTick();
}

namespace {

bool run_power_on_self_test() {
    return true;
}

void SystemClock_Config() {
}

void MX_GPIO_Init() {
}

}  // namespace

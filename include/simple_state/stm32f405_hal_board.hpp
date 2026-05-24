#pragma once

#include <cstdint>

#include "stm32f4xx_hal.h"

namespace simple_state {

struct Stm32f405RuntimeFlags {
    volatile bool fault_active{false};
    volatile bool self_test_passed{true};
};

struct Stm32f405HalBoardConfig {
    GPIO_TypeDef* led_port{};
    std::uint16_t led_pin{};
    GPIO_PinState led_active_state{GPIO_PIN_SET};

    GPIO_TypeDef* button_port{};
    std::uint16_t button_pin{};
    GPIO_PinState button_pressed_state{GPIO_PIN_SET};

    const Stm32f405RuntimeFlags* flags{};
    std::uint32_t (*tick_reader)(){HAL_GetTick};
};

class Stm32f405HalBoard {
public:
    explicit Stm32f405HalBoard(const Stm32f405HalBoardConfig& config) : config_(config) {}

    [[nodiscard]] std::uint32_t millis() const {
        return config_.tick_reader != nullptr ? config_.tick_reader() : 0U;
    }

    void set_led(bool is_on) {
        led_is_on_ = is_on;
        const GPIO_PinState pin_state = is_on ? config_.led_active_state : invert(config_.led_active_state);
        HAL_GPIO_WritePin(config_.led_port, config_.led_pin, pin_state);
    }

    [[nodiscard]] bool led_is_on() const {
        return led_is_on_;
    }

    [[nodiscard]] bool is_button_pressed() const {
        const GPIO_PinState sampled = HAL_GPIO_ReadPin(config_.button_port, config_.button_pin);
        return sampled == config_.button_pressed_state;
    }

    [[nodiscard]] bool has_fault() const {
        return config_.flags != nullptr ? config_.flags->fault_active : false;
    }

    [[nodiscard]] bool self_test_ok() const {
        return config_.flags != nullptr ? config_.flags->self_test_passed : true;
    }

private:
    static GPIO_PinState invert(GPIO_PinState state) {
        return state == GPIO_PIN_SET ? GPIO_PIN_RESET : GPIO_PIN_SET;
    }

    Stm32f405HalBoardConfig config_{};
    bool led_is_on_{};
};

}  // namespace simple_state

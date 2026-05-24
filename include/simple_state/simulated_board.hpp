#pragma once

#include <cstdint>
#include <vector>

namespace simple_state {

struct LedSample {
    std::uint32_t at_ms;
    bool is_on;
};

class SimulatedBoard {
public:
    [[nodiscard]] std::uint32_t millis() const {
        return now_ms_;
    }

    void set_time(std::uint32_t now_ms) {
        now_ms_ = now_ms;
    }

    void set_led(bool is_on) {
        led_on_ = is_on;
        led_history_.push_back({now_ms_, is_on});
    }

    [[nodiscard]] bool led_is_on() const {
        return led_on_;
    }

    void set_button_pressed(bool is_pressed) {
        button_pressed_ = is_pressed;
    }

    [[nodiscard]] bool is_button_pressed() const {
        return button_pressed_;
    }

    void set_fault(bool has_fault) {
        fault_ = has_fault;
    }

    [[nodiscard]] bool has_fault() const {
        return fault_;
    }

    void set_self_test_ok(bool ok) {
        self_test_ok_ = ok;
    }

    [[nodiscard]] bool self_test_ok() const {
        return self_test_ok_;
    }

    [[nodiscard]] const std::vector<LedSample>& led_history() const {
        return led_history_;
    }

private:
    std::uint32_t now_ms_{};
    bool led_on_{};
    bool button_pressed_{};
    bool fault_{};
    bool self_test_ok_{true};
    std::vector<LedSample> led_history_{};
};

}  // namespace simple_state

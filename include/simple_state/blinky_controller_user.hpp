#pragma once

#include "simple_state/generated/blinky_controller_generated.hpp"

namespace simple_state {

template <typename Board>
struct BlinkyControllerHooks {
    using Controller = BlinkyController<Board>;
    using Context = typename Controller::Context;

    struct Data {
        std::uint32_t fault_toggle_at{};
        bool fault_led_on{};
    };

    static void boot_on_enter(Context& context) {
        context.board.set_led(false);
    }

    static void boot_on_update(Context& context) {
        if (context.elapsed_in_state() < 100U) {
            return;
        }

        if (context.board.self_test_ok()) {
            context.template transition<typename Controller::IdleState>();
            return;
        }

        context.template transition<typename Controller::FaultState>();
    }

    static void boot_on_exit(Context&) {}

    static void idle_on_enter(Context& context) {
        context.board.set_led(false);
    }

    static void idle_on_update(Context& context) {
        if (context.board.has_fault()) {
            context.template transition<typename Controller::FaultState>();
            return;
        }

        if (context.board.is_button_pressed() || context.elapsed_in_state() >= 1000U) {
            context.template transition<typename Controller::LedOnState>();
        }
    }

    static void idle_on_exit(Context&) {}

    static void led_on_on_enter(Context& context) {
        context.board.set_led(true);
    }

    static void led_on_on_update(Context& context) {
        if (context.board.has_fault()) {
            context.template transition<typename Controller::FaultState>();
            return;
        }

        if (context.elapsed_in_state() >= 250U) {
            context.template transition<typename Controller::LedOffState>();
        }
    }

    static void led_on_on_exit(Context&) {}

    static void led_off_on_enter(Context& context) {
        context.board.set_led(false);
    }

    static void led_off_on_update(Context& context) {
        // if (context.board.has_fault()) {
        //     context.template transition<typename Controller::FaultState>();
        //     return;
        // }

        if (context.elapsed_in_state() >= 750U) {
            context.template transition<typename Controller::LedOnState>();
        }
    }

    static void led_off_on_exit(Context&) {}

    static void fault_on_enter(Context& context) {
        context.fault_toggle_at = context.now();
        context.fault_led_on = true;
        context.board.set_led(true);
    }

    static void fault_on_update(Context& context) {
        if ((context.now() - context.fault_toggle_at) < 100U) {
            return;
        }

        context.fault_toggle_at = context.now();
        context.fault_led_on = !context.fault_led_on;
        context.board.set_led(context.fault_led_on);
    }

    static void fault_on_exit(Context&) {}
};

}  // namespace simple_state

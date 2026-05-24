#pragma once

#include <cstdint>

#include "simple_state/crtp_state_machine.hpp"

namespace simple_state {

template <typename Board>
class BlinkyController {
public:
    struct BootState;
    struct IdleState;
    struct LedOnState;
    struct LedOffState;
    struct FaultState;

    struct Context {
        Board& board;
        Machine<Context>* machine{};
        std::uint32_t state_started_at{};
        std::uint32_t fault_toggle_at{};
        bool fault_led_on{};

        [[nodiscard]] std::uint32_t now() const {
            return board.millis();
        }

        void mark_state_entry() {
            state_started_at = now();
        }

        [[nodiscard]] std::uint32_t elapsed_in_state() const {
            return now() - state_started_at;
        }

        template <typename NextState>
        void transition() {
            machine->template transition_to<NextState>();
        }
    };

    struct BootState : State<BootState, Context> {
        static void on_enter(Context& context) {
            context.mark_state_entry();
            context.board.set_led(false);
        }

        static void on_update(Context& context) {
            if (context.elapsed_in_state() < 100U) {
                return;
            }

            if (context.board.self_test_ok()) {
                context.template transition<IdleState>();
                return;
            }

            context.template transition<FaultState>();
        }

        static void on_exit(Context&) {}

        static const char* name() {
            return "Boot";
        }
    };

    struct IdleState : State<IdleState, Context> {
        static void on_enter(Context& context) {
            context.mark_state_entry();
            context.board.set_led(false);
        }

        static void on_update(Context& context) {
            if (context.board.has_fault()) {
                context.template transition<FaultState>();
                return;
            }

            if (context.board.is_button_pressed() || context.elapsed_in_state() >= 1000U) {
                context.template transition<LedOnState>();
            }
        }

        static void on_exit(Context&) {}

        static const char* name() {
            return "Idle";
        }
    };

    struct LedOnState : State<LedOnState, Context> {
        static void on_enter(Context& context) {
            context.mark_state_entry();
            context.board.set_led(true);
        }

        static void on_update(Context& context) {
            if (context.board.has_fault()) {
                context.template transition<FaultState>();
                return;
            }

            if (context.elapsed_in_state() >= 250U) {
                context.template transition<LedOffState>();
            }
        }

        static void on_exit(Context&) {}

        static const char* name() {
            return "LedOn";
        }
    };

    struct LedOffState : State<LedOffState, Context> {
        static void on_enter(Context& context) {
            context.mark_state_entry();
            context.board.set_led(false);
        }

        static void on_update(Context& context) {
            if (context.board.has_fault()) {
                context.template transition<FaultState>();
                return;
            }

            if (context.elapsed_in_state() >= 750U) {
                context.template transition<LedOnState>();
            }
        }

        static void on_exit(Context&) {}

        static const char* name() {
            return "LedOff";
        }
    };

    struct FaultState : State<FaultState, Context> {
        static void on_enter(Context& context) {
            context.mark_state_entry();
            context.fault_toggle_at = context.now();
            context.fault_led_on = true;
            context.board.set_led(true);
        }

        static void on_update(Context& context) {
            if ((context.now() - context.fault_toggle_at) < 100U) {
                return;
            }

            context.fault_toggle_at = context.now();
            context.fault_led_on = !context.fault_led_on;
            context.board.set_led(context.fault_led_on);
        }

        static void on_exit(Context&) {}

        static const char* name() {
            return "Fault";
        }
    };

    explicit BlinkyController(Board& board) : context_{board}, machine_(context_) {
        context_.machine = &machine_;
    }

    void start() {
        machine_.template start<BootState>();
    }

    void run_once() {
        machine_.dispatch();
    }

    [[nodiscard]] const char* state_name() const {
        return machine_.current_name();
    }

    [[nodiscard]] bool led_is_on() const {
        return context_.board.led_is_on();
    }

private:
    Context context_;
    Machine<Context> machine_;
};

}  // namespace simple_state

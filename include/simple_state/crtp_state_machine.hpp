#pragma once

namespace simple_state {

template <typename Context>
struct StateOps {
    void (*enter)(Context&);
    void (*update)(Context&);
    void (*exit)(Context&);
    const char* (*name)();
};

template <typename Derived, typename Context>
struct State {
    static void enter(Context& context) {
        Derived::on_enter(context);
    }

    static void update(Context& context) {
        Derived::on_update(context);
    }

    static void exit(Context& context) {
        Derived::on_exit(context);
    }

    static const char* name() {
        return Derived::name();
    }

    inline static constexpr StateOps<Context> ops{
        &State::enter,
        &State::update,
        &State::exit,
        &State::name,
    };
};

template <typename Context>
class Machine {
public:
    explicit Machine(Context& context) : context_(context) {}

    template <typename InitialState>
    void start() {
        transition_to<InitialState>();
    }

    template <typename NextState>
    void transition_to() {
        if (current_ != nullptr) {
            current_->exit(context_);
        }

        current_ = &NextState::ops;
        current_->enter(context_);
    }

    void dispatch() {
        if (current_ != nullptr) {
            current_->update(context_);
        }
    }

    [[nodiscard]] const char* current_name() const {
        return current_ != nullptr ? current_->name() : "None";
    }

private:
    Context& context_;
    const StateOps<Context>* current_{};
};

}  // namespace simple_state

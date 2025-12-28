#![no_std]
#![no_main]

// imports
use esp_backtrace as _;
use esp_hal::{
    clock::ClockControl,
    delay::Delay,
    gpio::{Io, Level, Output, Pull, Input},
    peripherals::Peripherals,
    prelude::*,

    //led controller pwm
    ledc::{
        channel::{self, ChannelIFace},
        timer::{self, TimerIFace},
        LSGlobalClkSource, Ledc, LowSpeed,
    },
};


#[entry]
fn main() -> ! {

    let peripherals = Peripherals::take();

    //returns clock, software interrupt ctrl 
    let system = peripherals.SYSTEM.split();

    //sets clock to max speed, returns Clocks structure
    let clocks = ClockControl::max(system.clock_control).freeze();

    // creates delay timer by reading clock config (keeps ownership to clocks)
    let mut delay = Delay::new(&clocks);
}

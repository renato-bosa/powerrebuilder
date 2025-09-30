//! Iced GUI Emitter
//!
//! Generates Iced cross-platform GUI applications with Elm architecture.
//! Iced is a cross-platform GUI library for Rust inspired by Elm.

use domain::model::{CoreModule, UiNode, UiTree};
use domain::translation::{
    ui_to_iced, EmissionUnit, EmitErr, EmittedFile, FeatureSet, TargetEmitter,
};
use std::collections::HashMap;

/// Iced generator configuration
#[derive(Debug, Clone)]
pub struct IcedGeneratorConfig {
    pub app_name: String,
    pub app_title: String,
    pub version: String,
    pub window_width: u32,
    pub window_height: u32,
}

impl Default for IcedGeneratorConfig {
    fn default() -> Self {
        Self {
            app_name: "iced_app".to_string(),
            app_title: "Iced Application".to_string(),
            version: "0.1.0".to_string(),
            window_width: 800,
            window_height: 600,
        }
    }
}

pub struct IcedEmitter {
    config: IcedGeneratorConfig,
}

impl IcedEmitter {
    pub fn new(config: IcedGeneratorConfig) -> Self {
        Self { config }
    }

    /// Generate Cargo.toml with iced dependencies
    fn generate_cargo_toml(&self) -> String {
        format!(
            r#"[package]
name = "{}"
version = "{}"
edition = "2021"
authors = ["PowerBuilder Migration <migration@example.com>"]

[dependencies]
iced = {{ version = "0.12", features = ["tokio", "debug"] }}
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"

[[bin]]
name = "{}"
path = "src/main.rs"
"#,
            self.config.app_name, self.config.version, self.config.app_name
        )
    }

    /// Generate main.rs with Iced app
    fn generate_main_rs(&self, ui: &UiTree) -> String {
        let (window_title, _children) = match &ui.root {
            UiNode::Window { title, children } => (title.clone(), children),
            _ => (self.config.app_title.clone(), &vec![]),
        };

        format!(
            r#"//! {} - Iced GUI Application
//!
//! Generated from PowerBuilder UI using Iced framework.

use iced::{{executor, Application, Command, Element, Settings, Theme}};

mod state;
mod message;
mod view;
mod update;

use state::AppState;
use message::Message;

fn main() -> iced::Result {{
    App::run(Settings {{
        window: iced::window::Settings {{
            size: ({}, {}),
            ..Default::default()
        }},
        ..Default::default()
    }})
}}

/// Main application following The Elm Architecture
pub struct App {{
    state: AppState,
}}

impl Application for App {{
    type Executor = executor::Default;
    type Message = Message;
    type Theme = Theme;
    type Flags = ();

    fn new(_flags: Self::Flags) -> (Self, Command<Self::Message>) {{
        (
            Self {{
                state: AppState::new(),
            }},
            Command::none(),
        )
    }}

    fn title(&self) -> String {{
        "{}".to_string()
    }}

    fn update(&mut self, message: Self::Message) -> Command<Self::Message> {{
        update::update(&mut self.state, message)
    }}

    fn view(&self) -> Element<Self::Message> {{
        view::view(&self.state)
    }}

    fn theme(&self) -> Self::Theme {{
        Theme::Dark
    }}
}}
"#,
            self.config.app_title,
            self.config.window_width,
            self.config.window_height,
            window_title
        )
    }

    /// Generate state.rs
    fn generate_state(&self) -> String {
        r#"//! Application State
//!
//! The single source of truth for the application following The Elm Architecture.

use serde::{Deserialize, Serialize};

/// Application state - immutable, replaced on updates
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppState {
    /// Counter example
    pub counter: i32,

    /// Loading state
    pub is_loading: bool,

    /// Error message
    pub error: Option<String>,

    /// User input text
    pub input_text: String,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            counter: 0,
            is_loading: false,
            error: None,
            input_text: String::new(),
        }
    }
}

impl Default for AppState {
    fn default() -> Self {
        Self::new()
    }
}
"#
        .to_string()
    }

    /// Generate message.rs
    fn generate_message(&self) -> String {
        r#"//! Messages
//!
//! Events that trigger state updates following The Elm Architecture.

/// Messages that can be sent to update the application state
#[derive(Debug, Clone)]
pub enum Message {
    /// Increment counter
    Increment,

    /// Decrement counter
    Decrement,

    /// Reset counter to zero
    Reset,

    /// Input text changed
    InputChanged(String),

    /// Button clicked
    ButtonClicked,

    /// Async operation completed
    AsyncCompleted(Result<String, String>),
}
"#
        .to_string()
    }

    /// Generate update.rs
    fn generate_update(&self) -> String {
        r#"//! Update Logic
//!
//! Pure function that updates state based on messages.

use crate::message::Message;
use crate::state::AppState;
use iced::Command;

/// Update function: (State, Message) -> (State, Command)
pub fn update(state: &mut AppState, message: Message) -> Command<Message> {
    match message {
        Message::Increment => {
            state.counter += 1;
            Command::none()
        }

        Message::Decrement => {
            state.counter -= 1;
            Command::none()
        }

        Message::Reset => {
            state.counter = 0;
            Command::none()
        }

        Message::InputChanged(text) => {
            state.input_text = text;
            Command::none()
        }

        Message::ButtonClicked => {
            println!("Button clicked! Counter: {}", state.counter);
            Command::none()
        }

        Message::AsyncCompleted(result) => {
            match result {
                Ok(data) => {
                    println!("Async completed: {}", data);
                    state.is_loading = false;
                }
                Err(err) => {
                    state.error = Some(err);
                    state.is_loading = false;
                }
            }
            Command::none()
        }
    }
}
"#
        .to_string()
    }

    /// Generate view.rs
    fn generate_view(&self) -> String {
        r#"//! View Logic
//!
//! Pure function that renders UI from state.

use crate::message::Message;
use crate::state::AppState;
use iced::widget::{button, column, container, row, text, text_input, Space};
use iced::{Alignment, Element, Length};

/// View function: State -> Element<Message>
pub fn view(state: &AppState) -> Element<Message> {
    let counter_text = text(format!("Counter: {}", state.counter))
        .size(30);

    let increment_button = button(text("Increment"))
        .on_press(Message::Increment);

    let decrement_button = button(text("Decrement"))
        .on_press(Message::Decrement);

    let reset_button = button(text("Reset"))
        .on_press(Message::Reset);

    let buttons = row![increment_button, decrement_button, reset_button]
        .spacing(10)
        .align_items(Alignment::Center);

    let input = text_input("Enter text...", &state.input_text)
        .on_input(Message::InputChanged)
        .padding(10)
        .size(20);

    let action_button = button(text("Click Me"))
        .on_press(Message::ButtonClicked);

    let error_text = if let Some(ref err) = state.error {
        text(format!("Error: {}", err)).size(16)
    } else {
        text("")
    };

    let content = column![
        Space::with_height(Length::Fixed(20.0)),
        counter_text,
        Space::with_height(Length::Fixed(10.0)),
        buttons,
        Space::with_height(Length::Fixed(20.0)),
        input,
        Space::with_height(Length::Fixed(10.0)),
        action_button,
        Space::with_height(Length::Fixed(10.0)),
        error_text,
    ]
    .align_items(Alignment::Center)
    .spacing(10);

    container(content)
        .width(Length::Fill)
        .height(Length::Fill)
        .center_x()
        .center_y()
        .into()
}
"#
        .to_string()
    }

    /// Generate README.md
    fn generate_readme(&self) -> String {
        format!(
            r#"# {}

Cross-platform GUI application built with Iced framework.

## Features

- Cross-platform (Windows, macOS, Linux)
- Elm-inspired architecture
- Reactive UI
- Type-safe
- Fast and lightweight

## Build

```bash
cargo build --release
```

## Run

```bash
cargo run --release
```

## Development

```bash
# Run with hot-reload
cargo watch -x run

# Check code
cargo check

# Format code
cargo fmt

# Lint
cargo clippy
```

## Architecture

This application follows The Elm Architecture:

- **State**: Immutable application state (`state.rs`)
- **Message**: Events that trigger updates (`message.rs`)
- **Update**: Pure function that updates state (`update.rs`)
- **View**: Pure function that renders UI (`view.rs`)

## Generated by PowerRebuilder

This application was automatically generated from PowerBuilder UI using
the PowerRebuilder reverse engineering toolkit with Iced framework.
"#,
            self.config.app_title
        )
    }
}

impl TargetEmitter for IcedEmitter {
    fn target_id(&self) -> &'static str {
        "iced"
    }

    fn supports(&self, _features: &FeatureSet) -> bool {
        true // Iced supports all UI features
    }

    fn emit_core(&self, _ir: &CoreModule) -> Result<EmissionUnit, EmitErr> {
        // Iced emitter focuses on UI, not business logic
        // Use RustEmitter for core logic
        Ok(EmissionUnit {
            files: vec![],
            metadata: HashMap::new(),
        })
    }

    fn emit_ui(&self, ui: &UiTree) -> Result<EmissionUnit, EmitErr> {
        let mut files = vec![];

        // Convert UI to IcedView using domain translation
        let _iced_view = ui_to_iced(ui);

        // Generate Cargo.toml
        files.push(EmittedFile {
            path: "Cargo.toml".to_string(),
            content: self.generate_cargo_toml(),
            is_executable: false,
        });

        // Generate main.rs
        files.push(EmittedFile {
            path: "src/main.rs".to_string(),
            content: self.generate_main_rs(ui),
            is_executable: false,
        });

        // Generate state.rs
        files.push(EmittedFile {
            path: "src/state.rs".to_string(),
            content: self.generate_state(),
            is_executable: false,
        });

        // Generate message.rs
        files.push(EmittedFile {
            path: "src/message.rs".to_string(),
            content: self.generate_message(),
            is_executable: false,
        });

        // Generate update.rs
        files.push(EmittedFile {
            path: "src/update.rs".to_string(),
            content: self.generate_update(),
            is_executable: false,
        });

        // Generate view.rs
        files.push(EmittedFile {
            path: "src/view.rs".to_string(),
            content: self.generate_view(),
            is_executable: false,
        });

        // Generate README
        files.push(EmittedFile {
            path: "README.md".to_string(),
            content: self.generate_readme(),
            is_executable: false,
        });

        // Generate .gitignore
        files.push(EmittedFile {
            path: ".gitignore".to_string(),
            content: "/target\nCargo.lock\n".to_string(),
            is_executable: false,
        });

        Ok(EmissionUnit {
            files,
            metadata: HashMap::new(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_iced_emitter() {
        let config = IcedGeneratorConfig::default();
        let emitter = IcedEmitter::new(config);
        assert_eq!(emitter.target_id(), "iced");
    }

    #[test]
    fn test_generate_cargo_toml() {
        let config = IcedGeneratorConfig::default();
        let emitter = IcedEmitter::new(config);
        let cargo = emitter.generate_cargo_toml();
        assert!(cargo.contains("[package]"));
        assert!(cargo.contains("iced"));
    }
}

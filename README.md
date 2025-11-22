# JMRecipes

**JMRecipes** is a static recipe website generator.

See a live demonstration here: [**JMRecipes Demo**](https://realjoemay.github.io/jmr-demo/)


## Features

- **Cost and Nutrition Calculations**: Compute cost and nutrition from ingredients.
- **Multiple Scales**: Adjust recipes for different serving sizes.
- **Copy Ingredients**: Easily copy a list of ingredients to your clipboard.
- **Linked Recipes**: A recipe can be an ingredient to another recipe.
- **Print Page**: Includes print-friendly recipe pages.
- **Powerful Search**: Find recipes by title or ingredients.
- **Dark Theme**: Everything should have dark theme.
- **Free Hosting**: Host your static recipe website on **GitHub Pages** at no cost.
- **And More!**


## Getting Started

Follow these steps to set up your local environment.

### Prerequisites

- Python 3.12+
- pip for package management
- Optional: virtualenv (recommended)

### 1. Clone the repository
```bash
git clone https://github.com/realJoeMay/jmrecipes.git
cd jmrecipes
```

### 2. Create/activate virtual environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the project in editable mode
```bash
python -m pip install --upgrade pip #upgrade pip
pip install -e .
```

### 4. CLI Usage

```bash
# Check available commands
jmrecipes --help

# Build the site
jmrecipes build

# run built in test
pytest
```

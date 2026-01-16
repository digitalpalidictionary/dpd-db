---
name: dpd-gui-development
description: Develop and modify the Digital Pāḷi Dictionary GUI using Flet framework for lexicographer tools
tags: [dpd, gui, flet, python, lexicography]
version: 1.0.0
author: DPD Team
dependencies: []
---
# DPD GUI Development

## When to use this skill
Use this skill when you need to develop, modify, or troubleshoot the Digital Pāḷi Dictionary GUI. This skill is essential for creating and maintaining the lexicographer tools that allow users to add, edit, and verify Pāḷi dictionary data with real-time integrity checks.

## Instructions
1. Import necessary Flet components and DPD-specific modules
2. Follow the existing GUI architecture patterns in the gui2 directory
3. Use the established dpd_fields classes for form elements
4. Implement proper data validation before saving to the database
5. Follow the existing code style and UI patterns

## Examples

### Basic Flet page setup:
```python
import flet as ft
from dpd_fields import DpdField
from database_manager import DatabaseManager

def main(page: ft.Page):
    page.title = "Digital Pāḷi Dictionary Editor"
    page.scroll = ft.ScrollMode.AUTO
    
    # Initialize database connection
    db_manager = DatabaseManager()
    
    # Add your UI elements here
    page.add(ft.Text("DPD Editor"))
    
ft.app(target=main)
```

### Creating a word entry form:
```python
from dpd_fields import DpdField
from dpd_fields_meaning import MeaningField
from dpd_fields_compound_construction import CompoundConstructionField

def create_word_entry_form(page: ft.Page):
    # Create form fields using existing DPD field classes
    word_field = DpdField("Word", "lemma_1")
    pos_field = DpdField("Part of Speech", "pos")
    meaning_field = MeaningField()
    compound_field = CompoundConstructionField()
    
    # Create form layout
    form = ft.Column([
        word_field.get_control(),
        pos_field.get_control(),
        meaning_field.get_control(),
        compound_field.get_control()
    ])
    
    return form
```

### Adding a save button with validation:
```python
def create_save_button(db_manager, data_dict):
    def save_word(e):
        # Validate required fields
        if not data_dict.get('lemma_1'):
            page.snack_bar = ft.SnackBar(ft.Text("Word field is required"))
            page.snack_bar.open = True
            page.update()
            return
        
        # Save to database
        try:
            db_manager.save_word(data_dict)
            page.snack_bar = ft.SnackBar(ft.Text("Word saved successfully"))
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error saving word: {str(ex)}"))
        
        page.snack_bar.open = True
        page.update()
    
    return ft.ElevatedButton("Save Word", on_click=save_word)
```

## Best Practices
- Follow the existing architecture in the gui2 directory
- Use the established dpd_fields classes for consistency
- Implement proper error handling and user feedback
- Validate data before saving to the database
- Use the existing DatabaseManager for database operations
- Follow Flet's responsive design principles
- Maintain consistency with the existing UI/UX patterns
- Use the established color scheme and typography from identity/css/
- Test forms with both valid and invalid inputs
- Implement proper session management for multi-user scenarios

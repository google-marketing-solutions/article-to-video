import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatInputModule } from '@angular/material/input';
import { FormControl } from '@angular/forms';

@Component({
  selector: 'article-text-input',
  standalone: true,
  imports: [MatInputModule],
  templateUrl: './article_text_input.component.html',
  styleUrl: './article_text_input.component.css'
})
export class ArticleTextInput {
  @Output() textChanged = new EventEmitter<string>();

  updateTextArea(event: Event) {
    const newValue = (event.target as HTMLInputElement).value;
    this.textChanged.emit(newValue);
  }
}

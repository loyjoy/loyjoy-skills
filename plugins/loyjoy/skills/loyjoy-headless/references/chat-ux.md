# Chat UX: building attractive chat agents

Read this before creating a customer-facing chat agent or prototype, and whenever the user asks to make an agent look better or more modern. The rules aim at a calm, premium, app-like look in the spirit of Apple and Trade Republic: lots of white space, restrained color, large clear typography, one-tap interactions. They use only standard LoyJoy modules and branding attributes. They apply to every brand; take the concrete colors from the customer. Resolve every attribute name against the schema before writing, as SKILL.md requires.

## 1. Color and branding

1. Restraint beats brand saturation. Most of the chat is white or light neutral; the brand color marks only what matters.
2. Agent messages are the `Send` bubble, user answers the `Receive` bubble (named from the widget's point of view). Give agent messages a light neutral background with dark text, and user answers the brand color with white text. Saturated agent bubbles make the chat look like a form.
3. Use exactly one accent color, reserved for the primary call to action (`loyjoy:widgetButtonPrimaryColor`). Do not repeat it on secondary elements such as the send icon (`loyjoy:widgetChatFooterSendColor`).
4. Answer options must look different from sent answers. Use outlined quick replies (`loyjoy:widgetQuickReplyFilledDisable` `true`) with rounded corners.
5. Keep the header plain: white, logo centered, no redundant title. Do not set `loyjoy:widgetChatHeaderTitleTextAlign` to `left`, it shifts the logo off center.
6. Pace the conversation briskly (`loyjoy:widgetTypingMode` `fast`).
7. For prototypes shown to customers, hide the LoyJoy watermark (`loyjoy:widgetWatermarkDisable` `true`) if the tenant's plan allows it.
8. Derive colors, button shapes and icon style from the customer's live website. If no official style guide is available, say so and ask the customer for it.

## 2. Questions and answers

1. Avoid form patterns. Never use `single_choice` (radio buttons plus a confirm button) for navigation. Use `quick_reply` for short answers and `single_choice_icon` for visual choices. Both work with one tap.
2. Changing a question type with `data_collection_question_put` keeps question and answer ids, so split conditions keep working.
3. One short question per message. No numbering, no bullet lists explaining the options. Answer labels of at most three or four words.
4. Start with the easy, relevant questions. Move sensitive or rarely relevant ones to the end (`bpmn_process_element_move_post`).

## 3. Icons and images

1. Icons for icon tiles: square PNG, 256 × 256 px, transparent background, about 30 % padding on each side. The widget scales the image to the full tile width, so icons without padding touch the tile edges and look crude.
2. Icon style: simple line icons in the brand's dark color with one element in the accent color. Keep stroke width and corner style consistent across a set.
3. Product images: 1200 × 630 px, one large key message plus one icon or visual. Do not repeat text the card already shows, such as provider or product name. Small text inside images becomes unreadable on phones.
4. Set alt texts for every image (i18n `asset_alt/<asset-id>`). The model check reports `NO_A11Y` when they are missing.
5. Assets cannot be uploaded through MCP. Hand the files to the user and name exactly where each one goes.

## 4. Product cards

1. When a card should lead somewhere in the flow, give it a button of type `variable` (`variable_key`, `variable_literal`, button text in i18n `products_product_button/<product-id>`). Only then does the products module wait for a click; otherwise the agent keeps writing past the cards. Branch on the variable afterwards.
2. A product URL (`products_product_url/<product-id>`) makes title and image clickable, independent of the button type.
3. Keep descriptions to at most three short lines.

## 5. Comparisons

1. For comparing two or three options, a web component table looks far more polished than cards side by side. Lead with the single most important difference as a large figure or visual, then a few rows. Show the selected option clearly.
2. The component dispatches `CustomEvent('variables', {detail: {variables: {...}, continue: true}})`. LoyJoy stores each variable as `<key>_<module-id with non-alphanumerics replaced by _>`.
3. After copying a process, conditions still reference the variable names of the old module ids; the copy does not remap them. Grep for the old suffix and patch every `lhsVariable`.
4. Web components only render in the published agent. Publish before testing.
5. Escape all non-ASCII characters in the JavaScript (`ä`), otherwise umlauts break.

## 6. Texts and flow

1. One or two lines per message. Remove anything a card, table or image already shows.
2. Frame recommendations positively and put restrictions on the card or in the table, not at the start of a message.
3. Never end in a dead end. Close the guided part with a quick reply offering the next steps, and give each option a short reaction (`data_collection_answer_option_response/<option-id>`).

## 7. Verify visually

1. After the user publishes, open the published agent at phone size (390 × 844 px) and click through every path.
2. Check: options clearly distinct from answers, no form-like elements, no text walls, cards and tables fully visible, icons with breathing room, a clear next step at the end.
3. Show the user screenshots before calling a redesign finished.

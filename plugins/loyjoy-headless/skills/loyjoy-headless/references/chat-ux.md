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

## 5. Web components: interactive cards

A `WEB_COMPONENT_SUBPROCESS` renders custom UI inside the chat. Use it where standard modules look like a form. A tested starter with a configurator and a comparison card is in [web-component-starter.js](web-component-starter.js).

1. Offer an interactive card as an option for the core decision. When a flow asks many related questions to reach one decision (plan choice, product finder, configurator, calculator), propose to the user one card instead of a button questionnaire: all inputs on one card, the result updates live (recommendation, one key figure, a short reason, optionally a small chart), one primary button, and the card locks with a confirmation after submit. Keep a questionnaire for single remaining fields. Do not impose it; a short button questionnaire is still the better choice for short, simple or highly regulated flows.
2. For comparing two or three options, a web component table looks far more polished than cards side by side. Lead with the most important difference as a large figure, then a few rows. Highlight the recommended option and show the selected one clearly.
3. Output: the component dispatches `CustomEvent('variables', {detail: {variables: {...}, continue: true}, bubbles: true, composed: true})`. LoyJoy stores each variable scoped as `<key>_<module id with non-alphanumerics replaced by _>`, never under the plain key.
4. Copy the results back. Place a `VARIABLE_SUBPROCESS` (`loyjoy:variableVariableStore` `session`) right after the card, with one `variableAssignment` per field: `key` is the plain name, `expression` is `<key>_<module_id>`. Otherwise prompts, mails, API mappings and conditions that use the plain names stay empty.
5. Input: pass values into the card with `mapping` elements of type `prop` (`source_variable`, `target_field`). Pass the language as a `lang` prop with `source_expression` `displayLanguage()`. The component receives all props as one JSON object on its `properties` property or attribute.
6. Combine the card with the AI agent. Feed the card the same plain variables that the agent's `variables_set` tools write. Then details typed as free text pre-fill the card when the flow returns to it. Tell the agent in its custom instruction which cards exist, that it must not repeat their options, and that saved values pre-fill them.
7. Keep one source of truth. If a card and an AI prompt both produce a recommendation, pass the card's result into the prompt and instruct the model to use it unchanged. Two independent recommendations will eventually contradict each other.
8. Design: Shadow DOM, inherit the chat font, take colors from the process branding, max width about 440 px, test at 390 px. One large result figure, compact controls (segmented buttons, steppers, tiles with inline SVG icons), short labels. Mark example figures and indicative prices as such on the card. Show real prices or tariffs only when the customer provides them.
9. Hosting: assets cannot be uploaded through MCP. For prototypes, minify the script and set `loyjoy:webComponentUrl` to `data:text/javascript;base64,<base64 of the UTF-8 file>`. Base64 keeps umlauts and accents intact without escaping. One bundle can define several custom elements; give every module a URL that loads the bundle. For production, upload the file as module asset in the Manager or host it on the customer's CDN.
10. After copying a process, conditions and variable assignments still reference the variable names of the old module ids; the copy does not remap them. Grep for the old suffix and patch every `lhsVariable` and `expression`.
11. Test in two stages. First render the component locally in a headless browser with sample props and log the `variables` event. Web components only render in the published agent, so after the user approves publishing, click through the published agent end to end, including a free-text message while a card is open.

## 6. Texts and flow

1. One or two lines per message. Remove anything a card, table or image already shows.
2. Frame recommendations positively and put restrictions on the card or in the table, not at the start of a message.
3. Never end in a dead end. Close the guided part with a quick reply offering the next steps, and give each option a short reaction (`data_collection_answer_option_response/<option-id>`).

## 7. Verify visually

1. After the user publishes, open the published agent at phone size (390 × 844 px) and click through every path.
2. Check: options clearly distinct from answers, no form-like elements, no text walls, cards and tables fully visible, icons with breathing room, a clear next step at the end.
3. Show the user screenshots before calling a redesign finished.

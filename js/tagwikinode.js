// NOTE: i have almost 0 clue how any of this works

import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";
// NOTE: code for show text is taken from https://github.com/pythongosssss/ComfyUI-Custom-Scripts/blob/main/web/js/showText.js
app.registerExtension({
    name: "BooruToolkit.TagWikiNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "TagWikiFetch") {
            // Store the original onConfigure method
            const onConfigure = nodeType.prototype.onConfigure;
            
            // Override the onConfigure method to add a button
            nodeType.prototype.onConfigure = function () {
                // Call the original onConfigure method if it exists
                onConfigure?.apply(this, arguments);
// BLESS DEEPSEEK V3
                // Add a button widget
                this.addWidget("button", "I don't do anything", "Button", () => {
                    alert("Button clicked! u stink btw");
                });
            };

            // Create a text widget to display the input string
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);

                // Clear existing widgets (if any)
                if (this.widgets) {
                    // Set the number of widgets to preserve (e.g., 2 for the first two widgets)
                    const widgetsToPreserve = 4; // hardcoded thing because I don't know JS

                    // Remove widgets starting from the end to avoid index issues
                    for (let i = this.widgets.length - 1; i >= widgetsToPreserve; i--) {
                        this.widgets[i].onRemove?.(); // Call the widget's cleanup function
                        this.widgets.pop(); // Remove the widget from the array
                    }
                }

                // Create a new text widget to display the input string
                const widget = ComfyWidgets["STRING"](this, "text", ["STRING", { multiline: true }], app).widget;
                widget.inputEl.readOnly = true;
                widget.inputEl.style.opacity = 0.9; // Adjust opacity for better readability
                widget.value = message.text.join(""); // Display all strings in the list, separated by newlines

                // Resize the widget to fit the text, doesn't resize node
                requestAnimationFrame(() => {
                    const sz = this.computeSize();
                    if (sz[0] < this.size[0]) {
                        sz[0] = this.size[0];
                    }
                    if (sz[1] < this.size[1]) {
                        sz[1] = this.size[1];
                    }
                    this.onResize?.(sz);
                    app.graph.setDirtyCanvas(true, false);
                });
            };
        }
    },
});
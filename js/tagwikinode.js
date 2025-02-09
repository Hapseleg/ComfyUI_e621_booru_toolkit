// NOTE: i have almost 0 clue how any of this works

import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
    name: "BooruToolkit.TagWikiNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "TagWikiFetch") {
            // Store the original onConfigure method
            const onConfigure = nodeType.prototype.onConfigure;

            // Override the onConfigure method to add a button
            nodeType.prototype.onNodeCreated = function () {
                // Call the original onConfigure method if it exists
                onConfigure?.apply(this, arguments);
                // BLESS DEEPSEEK V3
                // Add a button widget

                const buttonWidget = this.addWidget("button", "Fetch Wiki", "Button", async () => {
                    buttonWidget.disabled = true;
                    buttonWidget.name = "Loading...";
                    this.onResize?.(this.computeSize()); // Refresh the UI

                    try {
                        // Get values from all three widgets
                        const tagInputWidget = this.widgets[0];    // "tags" string input
                        const booruWidget = this.widgets[1];       // "booru" dropdown
                        const extendedInfoWidget = this.widgets[2]; // "extended_info" dropdown

                        if (!tagInputWidget || !booruWidget || !extendedInfoWidget) {
                            throw new Error("Missing required widgets!");
                        }

                        // Prepare request data with all values
                        const requestData = {
                            tag: tagInputWidget.value,
                            booru: booruWidget.value,
                            extended_info: extendedInfoWidget.value,
                            node_id: this.id
                        };

                        // Send request to Python endpoint
                        const response = await fetch("/booru/tag_wiki", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify(requestData),
                        }); // https://docs.comfy.org/essentials/comfyui-server/comms_routes#custom-routes bit different but ig it works eh

                        // Handle response
                        const result = await response.json();
                        if (result.error) {
                            throw new Error(result.error);
                        }

                        // Process successful response
                        const responseData = result.data || "Received empty response - Likely nothing found.";

                        updateTextWidget(this, responseData);
                    } catch (error) {
                        alert(`error? ${error}`);
                        updateTextWidget(this, error);
                    } finally {
                        // Revert button text to "Fetch Wiki"
                        buttonWidget.name = "Fetch Wiki";
                        buttonWidget.disabled = false;
                        this.onResize?.(this.computeSize()); // Refresh the UI
                    }
                });
            };

            // Create a text widget to display the input string
            const onExecuted = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function (message) {
                onExecuted?.apply(this, arguments);
                let resultText = message?.text;
                if (Array.isArray(resultText)) {
                    resultText = resultText.join(""); // Join array elements into a single string
                } else {
                    resultText = JSON.stringify(message); // Fallback to stringifying the object
                }
                //alert(resultText)
                updateTextWidget(this, resultText);
            };
        }
    },
});


// Reusable function to update the text widget
function updateTextWidget(node, message) {
    //alert(`stink ${JSON.stringify(message)}`);

    // Clear existing widgets (if any)
    if (node.widgets) {
        // Set the number of widgets to preserve (e.g., 2 for the first two widgets)
        const widgetsToPreserve = 4; // hardcoded thing because I don't know JS

        // Remove widgets starting from the end to avoid index issues
        for (let i = node.widgets.length - 1; i >= widgetsToPreserve; i--) {
            node.widgets[i].onRemove?.(); // Call the widget's cleanup function
            node.widgets.pop(); // Remove the widget from the array
        }
    }

    // Create a new text widget to display the input string
    const widget = ComfyWidgets["STRING"](node, "text", ["STRING", { multiline: true }], app).widget;
    widget.inputEl.readOnly = true;
    widget.inputEl.style.opacity = 0.925; // Adjust opacity for better readability
    //widget.value = message.text.join(""); // Display all strings in the list, separated by newlines
    widget.value = message; // Display all strings in the list, separated by newlines

    // Resize the widget to fit the text, doesn't resize node
    requestAnimationFrame(() => {
        const sz = node.computeSize();
        if (sz[0] < node.size[0]) {
            sz[0] = node.size[0];
        }
        if (sz[1] < node.size[1]) {
            sz[1] = node.size[1];
        }
        node.onResize?.(sz);
        app.graph.setDirtyCanvas(true, false);
    });
}

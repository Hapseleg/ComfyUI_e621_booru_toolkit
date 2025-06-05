import { app } from "/scripts/app.js";

app.registerExtension({
    name: "Comfy.E621BooruToolkit.GetRandomBooruPost.ConditionalAPI",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "GetRandomBooruPost") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                const siteWidget = this.widgets.find(w => w.name === "site");
                const apiLoginWidget = this.widgets.find(w => w.name === "API_LOGIN");
                const apiKeyWidget = this.widgets.find(w => w.name === "API_KEY");

                if (!siteWidget || !apiLoginWidget) {
                    console.warn("E621 Booru Toolkit: Could not find 'site' or 'API' widget for GetRandomBooruPost.");
                    return r;
                }

                // Function to toggle API widget visibility
                const toggleApiVisibility = () => {
                    if (siteWidget.value !== "danbooru") {
                        apiLoginWidget.hidden = true;
                        apiKeyWidget.hidden = true;
                    } else {
                        apiLoginWidget.hidden = false;
                        apiKeyWidget.hidden = false;
                    }
                    // Trigger a resize to ensure the node UI updates correctly
                    this.computeSize();
                    app.graph.setDirtyCanvas(true, true);
                };

                // Store original onchange and wrap it
                const originalSiteOnchange = siteWidget.callback;
                siteWidget.callback = (value, ...args) => {
                    if (originalSiteOnchange) {
                        originalSiteOnchange.call(this, value, ...args);
                    }
                    toggleApiVisibility();
                };

                // Initial check
                toggleApiVisibility();

                return r;
            };
        }
    }
});

document.addEventListener("alpine:init", () => {
  Alpine.store("ui", {
    menuOpen: false,
    toggleMenu() {
      this.menuOpen = !this.menuOpen;
    },
  });

  Alpine.data("reveal", () => ({
    visible: false,
    init() {
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              this.visible = true;
              observer.disconnect();
            }
          });
        },
        { threshold: 0.2 }
      );
      observer.observe(this.$el);
    },
  }));
});

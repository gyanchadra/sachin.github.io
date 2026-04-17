function toggleMenu() {
    const menu = document.getElementById("sideMenu");
    const icon = document.getElementById("menuIcon");
    const overlay = document.getElementById("overlay");

    menu.classList.toggle("active");
    overlay.classList.toggle("active");

    if (menu.classList.contains("active")) {
        icon.classList.remove("fa-bars");
        icon.classList.add("fa-xmark");
    } else {
        icon.classList.remove("fa-xmark");
        icon.classList.add("fa-bars");
    }
}
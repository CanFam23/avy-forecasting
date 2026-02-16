import {useState} from "react";
import {Menu, X} from "lucide-react";
import type {navbarProps, hamProps} from "../types.ts";

export default function Navbar({navNames}: navbarProps) {
    // TODO: Change to links to navigate between pages
    const navHTML = navNames.map((name) => (
        <p
            key={name}
            className="font-bold p-2 hover:underline hover:cursor-pointer"
        >
            {name}
        </p>
    ));

    const [displayHamMenu, setDisplayHamMenu] = useState(false);

    return <header>
        <nav className="bg-[var(--color-primary)] text-white w-full p-5 flex shadow-md">
            <h1 className="font-extrabold text-5xl hover:cursor-pointer">AvyAI</h1>
            <div className="hidden sm:flex h-full items-baseline space-x-4 ml-10">
                {navHTML}
            </div>
            <button
                onClick={() => setDisplayHamMenu(true)}
                className="sm:hidden w-full"
                aria-label="Open navigation menu"
            >
                {/*Hide nav menu when ham menu is displayed*/}
                <Menu className="sm:hidden ml-auto mr-3 size-10 hover:cursor-pointer"/>
            </button>
            <Hamburger
                navHTML={navHTML}
                display={displayHamMenu}
                setDisplay={setDisplayHamMenu}
            />
        </nav>
    </header>;
}

function Hamburger({navHTML, display, setDisplay}: hamProps) {
    if (!display) return null;

    return (
        <>
            <div
                onClick={() => setDisplay(false)}
                className="fixed inset-0 z-40 bg-black/20"
            />

            <nav
                className="fixed top-0 right-0 z-50 flex h-full flex-col
                   bg-[var(--color-primary)] border-l-2 border-black p-2
                   animate-slide-in"
            >
                <button
                    onClick={() => setDisplay(false)}
                    className="ml-auto mr-2 mt-3"
                >
                    <X size={30} className="hover:cursor-pointer"/>
                </button>
                {navHTML}
            </nav>
        </>
    );
}

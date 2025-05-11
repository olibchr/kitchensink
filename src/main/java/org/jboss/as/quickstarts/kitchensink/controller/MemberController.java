package org.jboss.as.quickstarts.kitchensink.controller;

import jakarta.validation.Valid;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class MemberController {

    private final MemberService memberService;

    @Autowired
    public MemberController(MemberService memberService) {
        this.memberService = memberService;
    }

    @GetMapping("/")
    public String home(Model model) {
        // Always add an empty member object and the member list
        if (!model.containsAttribute("newMember")) {
            model.addAttribute("newMember", new Member());
        }
        model.addAttribute("members", memberService.findAllOrderedByName());
        return "index";
    }

    @PostMapping("/members")
    public String register(@Valid @ModelAttribute("newMember") Member member,
            BindingResult result,
            Model model,
            RedirectAttributes redirectAttributes) {

        // If validation errors, return to the form with errors
        if (result.hasErrors()) {
            model.addAttribute("members", memberService.findAllOrderedByName());
            return "index";
        }

        try {
            // Register the member
            memberService.register(member);
            // Add success message as flash attribute (will survive the redirect)
            redirectAttributes.addFlashAttribute("successMessage", "Registration successful!");
            // Redirect to home page (PRG pattern - Post/Redirect/Get)
            return "redirect:/";
        } catch (Exception e) {
            // Add error message and return to form
            model.addAttribute("members", memberService.findAllOrderedByName());
            model.addAttribute("errorMessage", getRootErrorMessage(e));
            return "index";
        }
    }

    private String getRootErrorMessage(Exception e) {
        // Default to general error message that registration failed.
        String errorMessage = "Registration failed. See server log for more information";

        if (e == null) {
            // This shouldn't happen, but return the default messages
            return errorMessage;
        }

        // Start with the exception and recurse to find the root cause
        Throwable t = e;
        while (t != null) {
            // Get the message from the Throwable class instance
            errorMessage = t.getLocalizedMessage();
            t = t.getCause();
        }

        // This is the root cause message
        return errorMessage;
    }
}
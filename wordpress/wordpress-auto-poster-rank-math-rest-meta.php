<?php
/**
 * Plugin Name: WordPress Auto Poster - Rank Math REST Meta
 * Description: Exposes Rank Math SEO title, description, focus keyword, and permalink fields to the WordPress REST API for WordPress Auto Poster.
 * Version: 1.1.1
 * Author: WordPress Auto Poster
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('init', function () {
    $post_types = get_post_types(array('show_in_rest' => true), 'names');
    $meta_fields = array(
        'rank_math_title' => 'sanitize_text_field',
        'rank_math_description' => 'sanitize_textarea_field',
        'rank_math_focus_keyword' => 'sanitize_text_field',
        'rank_math_permalink' => 'sanitize_text_field',
    );

    foreach ($post_types as $post_type) {
        foreach ($meta_fields as $meta_key => $sanitize_callback) {
            register_post_meta($post_type, $meta_key, array(
                'type' => 'string',
                'single' => true,
                'show_in_rest' => true,
                'sanitize_callback' => $sanitize_callback,
                'auth_callback' => function () {
                    return current_user_can('edit_posts');
                },
            ));
        }
    }
});

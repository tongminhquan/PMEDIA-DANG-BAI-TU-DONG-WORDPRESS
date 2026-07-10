<?php
/**
 * Plugin Name: PMEDIA - ĐĂNG BÀI TỰ ĐỘNG WORDPRESS - Rank Math REST Meta
 * Description: Exposes Rank Math SEO title, description, focus keyword, and permalink fields to the WordPress REST API for PMEDIA - ĐĂNG BÀI TỰ ĐỘNG WORDPRESS.
 * Version: 1.2.0
 * Author: PMEDIA
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

/**
 * Normalize primary and secondary keywords to Rank Math's comma-separated value.
 */
function pmedia_normalize_focus_keywords($value) {
    if (is_string($value)) {
        $value = preg_split('/[,;|\r\n]+/u', $value);
    }
    if (!is_array($value)) {
        return array();
    }

    $keywords = array();
    $seen = array();
    foreach ($value as $item) {
        $keyword = sanitize_text_field((string) $item);
        $keyword = trim($keyword);
        if ($keyword === '') {
            continue;
        }
        $key = function_exists('mb_strtolower') ? mb_strtolower($keyword, 'UTF-8') : strtolower($keyword);
        if (isset($seen[$key])) {
            continue;
        }
        $seen[$key] = true;
        $keywords[] = $keyword;
    }
    return array_slice($keywords, 0, 100);
}

add_action('rest_api_init', function () {
    register_rest_route('pmedia/v1', '/posts/(?P<id>\d+)/seo', array(
        'methods' => WP_REST_Server::EDITABLE,
        'permission_callback' => function ($request) {
            return current_user_can('edit_post', (int) $request['id']);
        },
        'callback' => function ($request) {
            $post_id = (int) $request['id'];
            if (!get_post($post_id)) {
                return new WP_Error('pmedia_post_not_found', 'Bài viết không tồn tại.', array('status' => 404));
            }

            $keywords = pmedia_normalize_focus_keywords($request->get_param('focus_keywords'));
            update_post_meta($post_id, 'rank_math_focus_keyword', implode(',', $keywords));

            if ($request->has_param('seo_title')) {
                update_post_meta($post_id, 'rank_math_title', sanitize_text_field($request->get_param('seo_title')));
            }
            if ($request->has_param('meta_description')) {
                update_post_meta($post_id, 'rank_math_description', sanitize_textarea_field($request->get_param('meta_description')));
            }
            if ($request->has_param('permalink')) {
                update_post_meta($post_id, 'rank_math_permalink', sanitize_title($request->get_param('permalink')));
            }

            return rest_ensure_response(array(
                'post_id' => $post_id,
                'focus_keywords' => $keywords,
                'keyword_count' => count($keywords),
                'rank_math_focus_keyword' => get_post_meta($post_id, 'rank_math_focus_keyword', true),
            ));
        },
        'args' => array(
            'id' => array(
                'type' => 'integer',
                'required' => true,
            ),
            'focus_keywords' => array(
                'type' => 'array',
                'required' => true,
                'items' => array('type' => 'string'),
            ),
            'seo_title' => array('type' => 'string'),
            'meta_description' => array('type' => 'string'),
            'permalink' => array('type' => 'string'),
        ),
    ));
});
